import os
import json
import random
import re
import csv
import ssl
from datetime import datetime, timedelta
from io import BytesIO
from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify, make_response, flash, abort
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from google.cloud import vision
from google.oauth2 import service_account
import resend
import secrets
from dotenv import load_dotenv

# Fix SSL certificate issues on Windows
try:
    import certifi
    os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
    os.environ['SSL_CERT_FILE'] = certifi.where()
except ImportError:
    # If certifi is not available, disable SSL verification for development
    ssl._create_default_https_context = ssl._create_unverified_context
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

# Initialize Google Cloud Vision client with SSL handling
def get_vision_client():
    """Get Google Cloud Vision client with proper SSL configuration"""
    try:
        credentials_json = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_JSON')
        if not credentials_json:
            return None
            
        credentials_data = json.loads(credentials_json)
        credentials = service_account.Credentials.from_service_account_info(credentials_data)
        
        # Aggressive SSL fix for Windows
        import grpc
        
        # Set multiple SSL environment variables
        try:
            import certifi
            cert_path = certifi.where()
            os.environ['GRPC_DEFAULT_SSL_ROOTS_FILE_PATH'] = cert_path
            os.environ['SSL_CERT_FILE'] = cert_path
            os.environ['SSL_CERT_DIR'] = os.path.dirname(cert_path)
            os.environ['REQUESTS_CA_BUNDLE'] = cert_path
            os.environ['CURL_CA_BUNDLE'] = cert_path
            print(f"✅ SSL certificates configured: {cert_path}")
        except ImportError:
            print("⚠️ certifi not available, trying fallback SSL configuration")
            
        # Try to disable SSL verification as last resort for development
        try:
            # This is a development-only workaround
            os.environ['GRPC_SSL_CIPHER_SUITES'] = 'HIGH:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384'
        except:
            pass
            
        # Create client with transport options
        client = vision.ImageAnnotatorClient(credentials=credentials)
        return client
        
    except Exception as e:
        print(f"Warning: Google Vision client not initialized: {e}")
        return None

# Initialize the client
client = get_vision_client()


# --- ENVIRONMENT DETECTION ---
ENABLE_SELENIUM = os.getenv('ENABLE_SELENIUM') == '1'
ON_VERCEL = bool(os.getenv('VERCEL'))
HAS_SELENIUM_SUPPORT = ENABLE_SELENIUM and not ON_VERCEL

# Conditional Selenium imports - only in local dev environment
if HAS_SELENIUM_SUPPORT:
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            USE_WEBDRIVER_MANAGER = True
        except ImportError:
            USE_WEBDRIVER_MANAGER = False
        print("✅ Selenium support enabled for local development")
        
        # Keep track of active drivers for cleanup if needed
        active_drivers = []
    except ImportError:
        print("⚠️ Selenium not available - falling back to client-side only")
        HAS_SELENIUM_SUPPORT = False
else:
    print(f"🚫 Selenium disabled (ENABLE_SELENIUM={ENABLE_SELENIUM}, ON_VERCEL={ON_VERCEL})")

# --- APP SETUP ---
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'a_very_secret_key_for_development')

# Initialize Resend API key from environment variable
resend.api_key = os.environ.get('RESEND_API_KEY')

# File paths
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(APP_ROOT, 'static', 'Mobicite_Placeholder_Locations.csv')
TEMPLATE_PDF = os.path.join(APP_ROOT, 'static', 'base_template.pdf')

PROFILE_FILE = os.path.join('/tmp', 'profile.json') if os.environ.get("VERCEL") else os.path.join(APP_ROOT, 'profile.json')

# Vercel KV storage simulation using environment variables
def get_profile_key():
    """Get a unique profile key based on user session or default"""
    return os.environ.get('USER_PROFILE_DATA', None)


# --- SECURITY HELPERS ---
def is_local_request():
    """Check if request is from local machine (security check for Selenium)"""
    ip = request.remote_addr or ''
    return ip in ['127.0.0.1', '::1', 'localhost']

# --- PROFILE HELPERS ---
def save_profile(data):
    try:
        # For Vercel, we'll store in session (temporary) since files don't persist
        if os.environ.get("VERCEL"):
            # Store in Flask session as a workaround
            from flask import session
            session['user_profile'] = data
            session.permanent = True
        else:
            # Local development - use file
            with open(PROFILE_FILE, 'w') as f:
                json.dump(data, f)
    except Exception as e:
        print(f"Error saving profile: {e}")

def load_profile():
    """Load hardcoded profile - it's always the same user"""
    return {
        'first_name': 'Aaron',
        'last_name': 'Meisner',
        'license': 'M256112128808',
        'address': '661 Querbes',
        'city': 'Montreal',
        'province': 'Québec',
        'postal_code': 'H2V3W6',
        'country': 'Canada',
        'email': 'AAMM5845@GMAIL.COM'
    }

# --- AUTOFILL URL GENERATOR ---
def generate_autofill_url(user_profile, ticket_data):
    import urllib.parse
    base_url = "https://services.montreal.ca/plaidoyer/rechercher/en"
    plea_text = "I plead not guilty. The parking meter was paid for the entire duration that my vehicle was parked at this location."
    params = {
        "statement": ticket_data.get('ticket_number', ''),
        "first_name": user_profile.get('first_name', ''),
        "last_name": user_profile.get('last_name', ''),
        "address": user_profile.get('address', ''),
        "plea_reason": plea_text
    }
    query_string = urllib.parse.urlencode(params)
    return f"{base_url}?{query_string}"

# --- ROUTES ---
@app.route('/')
def index():
    profile = load_profile()
    return render_template('index.html', profile=profile)

@app.route('/sw.js')
def service_worker():
    response = make_response(send_file('sw.js'))
    response.headers['Content-Type'] = 'application/javascript'
    return response

@app.route('/api/get_profile')
def get_profile_api():
    """API endpoint to get profile data for frontend autofill"""
    profile = load_profile()
    return jsonify(profile)

@app.route('/setup_profile', methods=['GET', 'POST'])
def setup_profile():
    if request.method == 'POST':
        user_profile_data = {
            'first_name': request.form.get('first_name', ''),
            'last_name': request.form.get('last_name', ''),
            'license': request.form.get('license', ''),
            'address': request.form.get('address', ''),
            'city': request.form.get('city', ''),
            'province': request.form.get('province', 'Québec'),
            'postal_code': request.form.get('postal_code', ''),
            'country': request.form.get('country', 'Canada'),
            'email': request.form.get('email', '')
        }
        save_profile(user_profile_data)
        return redirect(url_for('index'))
    return render_template('profile_setup.html', profile=load_profile())

# --- PDF GENERATION & EMAIL SENDING ---
@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    data = request.form
    ticket_number = data.get('ticket_number')

    if not ticket_number or not ticket_number.isdigit() or len(ticket_number) != 9:
        return "Invalid ticket number.", 400

    transaction = ' 00003' + ''.join([str(random.randint(0, 9)) for _ in range(5)])
    reference_number = ' ' + ''.join([str(random.randint(0, 9)) for _ in range(18)])
    auth_code = ' ' + ''.join([str(random.randint(0, 9)) for _ in range(6)])
    response_code = ' 027'
    space_raw = data.get('space', '')
    space_cleaned = re.sub(r'[^A-Za-z0-9]', '', space_raw)
    space_caps = ''.join([char.upper() if char.isalpha() else char for char in space_cleaned])
    date_str = data.get('date')
    time_str = data.get('start_time')
    date_obj = datetime.strptime(date_str + ' ' + time_str, '%Y-%m-%d %H:%M')
    adjusted_date_obj = date_obj + timedelta(minutes=3)
    start_time = adjusted_date_obj.strftime('%Y-%m-%d, %H:%M')
    end_time = (adjusted_date_obj + timedelta(minutes=10)).strftime('%Y-%m-%d, %H:%M')
    date_line = f" {adjusted_date_obj.strftime('%a, %b %d, %Y at %I:%M %p')}"
    transaction_datetime = ' ' + adjusted_date_obj.strftime('%Y-%m-%d, %H:%M')

    values = {
        'Transaction number': transaction,
        'Authorization code': auth_code,
        'Response code': response_code,
        'Space number': ' ' + space_caps,
        'Start of session': ' ' + start_time,
        'End of session': ' ' + end_time,
        'Top date line': date_line,
        'Reference number': reference_number
    }

    # Create PDF overlay
    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=letter)
    with open(CSV_PATH, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            field, text = row['field'], values.get(row['field'], row['text'])
            x_pt, y_pt = float(row['x_in']) * 72, (11 - (float(row['y_in']) + 0.1584)) * 72
            c.setFont("Helvetica", 11)
            c.drawString(x_pt, y_pt, text)
    ref_x, ref_y = 2.0836 * 72, (11 - (6.6827 + 0.1584)) * 72
    c.drawString(ref_x, ref_y, reference_number)
    tx_x, tx_y = 1.9515 * 72, (11 - (4.8789 + 0.1584)) * 72
    c.drawString(tx_x, tx_y, transaction_datetime)
    c.save()
    packet.seek(0)

    output = PdfWriter()
    background = PdfReader(TEMPLATE_PDF)
    overlay = PdfReader(packet)
    page = background.pages[0]
    page.merge_page(overlay.pages[0])
    output.add_page(page)
    temp_pdf = BytesIO()
    output.write(temp_pdf)
    temp_pdf.seek(0)
    
    # Flatten PDF by converting to image and back to PDF
    try:
        from pdf2image import convert_from_bytes
        from PIL import Image
        
        # Convert PDF to image (high quality)
        images = convert_from_bytes(temp_pdf.read(), dpi=300, fmt='png')
        
        # Convert image back to PDF
        final_pdf_in_memory = BytesIO()
        if images:
            # Save as PDF
            images[0].save(final_pdf_in_memory, 'PDF', resolution=300.0, quality=95)
            final_pdf_in_memory.seek(0)
        else:
            # Fallback to original if conversion fails
            temp_pdf.seek(0)
            final_pdf_in_memory = temp_pdf
    except Exception as e:
        print(f"PDF flattening failed, using original: {e}")
        temp_pdf.seek(0)
        final_pdf_in_memory = temp_pdf

    # Send email with PDF (optional - app works without email)
    email_sent = False
    try:
        user_profile = load_profile()
        if not resend.api_key:
            print("Info: Email not configured (no RESEND_API_KEY)")
            flash('✅ PDF generated successfully! (Email not configured)', 'success')
        elif user_profile and user_profile.get('email'):
            print(f"Attempting to send email to: {user_profile['email']}")
            
            email_params = {
                "from": "Tickety <onboarding@resend.dev>",
                "to": [user_profile['email']],
                "subject": f"Your Parking Receipt for Ticket #{ticket_number}",
                "html": f"""
                <div style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
                    <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0px 2px 6px rgba(0,0,0,0.1);">
                        <h2 style="color: #333;">Hi {user_profile['first_name']},</h2>
                        <p>We've generated your parking receipt for ticket <strong>#{ticket_number}</strong>.</p>
                        <p>Please see the attached PDF receipt. You can use this receipt when fighting your parking ticket.</p>
                        <p style="margin-top: 30px; font-size: 13px; color: #666;">
                            This email was automatically generated by Tickety.
                        </p>
                    </div>
                </div>
                """,
                "attachments": [{
                    "filename": f"Tickety_Receipt_{ticket_number}.pdf",
                    "content": list(final_pdf_in_memory.getvalue())
                }],
            }
            
            # Aggressive SSL fix for Windows email sending
            import requests
            import urllib3
            session = requests.Session()
            
            # Try multiple SSL fixes
            ssl_fixed = False
            try:
                import certifi
                cert_path = certifi.where()
                session.verify = cert_path
                # Set multiple SSL environment variables for requests
                os.environ['REQUESTS_CA_BUNDLE'] = cert_path
                os.environ['CURL_CA_BUNDLE'] = cert_path
                print(f"✅ Email SSL configured with certifi: {cert_path}")
                ssl_fixed = True
            except ImportError:
                print("⚠️ certifi not available for email SSL")
            
            if not ssl_fixed:
                # Last resort - disable SSL verification for development
                print("⚠️ Disabling SSL verification for email (development only)")
                session.verify = False
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            # Use requests directly instead of resend library to control SSL
            response = session.post(
                'https://api.resend.com/emails',
                headers={
                    'Authorization': f'Bearer {resend.api_key}',
                    'Content-Type': 'application/json'
                },
                json=email_params,
                timeout=15
            )
            
            if response.status_code == 200:
                email_sent = True
                print(f"✅ Email sent successfully! Response: {response.text}")
                flash(f'✅ PDF generated and emailed to {user_profile["email"]}!', 'success')
            else:
                print(f"❌ Email failed: {response.status_code} - {response.text}")
                flash(f'✅ PDF generated! (Email failed: {response.status_code})', 'success')
        else:
            print("No email address found in profile")
            flash('✅ PDF generated successfully! (Add email to profile for auto-send)', 'success')
    except Exception as e:
        print(f"Email failed (continuing anyway): {e}")
        flash('✅ PDF generated successfully! (Email delivery failed - check API key)', 'success')

    # Always return PDF for download
    final_pdf_in_memory.seek(0)
    return send_file(
        final_pdf_in_memory,
        as_attachment=True,
        download_name=f'Tickety_Receipt_{ticket_number}.pdf',
        mimetype='application/pdf'
    )

@app.route('/scan-ticket', methods=['POST'])
def scan_ticket():
    # Try to get/reinitialize client if needed
    vision_client = client or get_vision_client()
    
    if not vision_client:
        return jsonify(success=False, message="OCR not configured. Check Google Cloud credentials."), 500
        
    if 'ticket_image' not in request.files:
        return jsonify(success=False, message="No image file provided."), 400
        
    file = request.files['ticket_image']
    if file.filename == '':
        return jsonify(success=False, message="No file selected."), 400
        
    try:
        print("Processing OCR request...")
        content = file.read()
        image = vision.Image(content=content)
        
        # Use the vision client with SSL handling
        response = vision_client.document_text_detection(image=image)
        
        if response.error.message:
            raise Exception(f"Vision API error: {response.error.message}")
            
        raw_text = response.full_text_annotation.text
        print(f"OCR extracted text: {raw_text[:100]}...")  # Log first 100 chars

        ticket_number, space_number, extracted_date, extracted_time = "", "", "", ""
        ticket_match = re.search(r'\b(\d{3})\s*(\d{3})\s*(\d{3})\b', raw_text)
        if ticket_match:
            ticket_number = "".join(ticket_match.groups())
        space_match = re.search(r'(PL\d+)', raw_text, re.IGNORECASE)
        if space_match:
            space_number = space_match.group(1).upper()
        date_time_match = (
            re.search(r'au\s+(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})', raw_text, re.IGNORECASE)
            or re.search(r'Date\s+de\s+signification:\s*(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})', raw_text, re.IGNORECASE)
            or re.search(r'\b(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})\b', raw_text)
        )
        if date_time_match:
            extracted_date, extracted_time = date_time_match.groups()

        return jsonify(success=True, ticket_number=ticket_number, space=space_number, date=extracted_date, start_time=extracted_time)
        
    except Exception as e:
        print(f"Google Cloud Vision failed: {e}")
        return jsonify(success=False, message=f"OCR failed: {str(e)}. Please enter ticket details manually."), 500

# Add autofill_script route to support in-browser fight ticket autofill
@app.route('/autofill_script')
def autofill_script():
    profile = load_profile()
    ticket_number = request.args.get('ticket_number', '')

    message = random.choice([
        "I had paid for parking through the app, but the officer issued the ticket just a few minutes before the transaction was processed. I have attached the receipt showing proof of payment.",
        "I am pleading not guilty because I paid for parking using the mobile app at the time of parking. The ticket was issued either just before or right after the payment was confirmed. I've included the receipt to show this.",
        "I received a parking ticket even though I had paid using the parking app. The ticket was likely issued within a very short window before the payment was processed. I’ve attached the app receipt showing the payment time as proof."
    ])

    return render_template('autofill_script.html', profile=profile, ticket_number=ticket_number, message=message)

@app.route('/fight-ticket')
def fight_ticket_redirect():
    ticket_number = request.args.get('ticket_number', '')
    return redirect(url_for('autofill_script', ticket_number=ticket_number))

@app.route('/fight_ticket_form')
def fight_ticket_form():
    """Render the enhanced fight ticket form with all options"""
    ticket_number = request.args.get('ticket_number', '')
    profile = load_profile()
    
    if not profile:
        flash('Please set up your profile first before fighting a ticket.', 'warning')
        return redirect(url_for('setup_profile'))
    
    # Generate explanation message
    explanation = random.choice([
        "I had paid for parking through the app, but the officer issued the ticket just a few minutes before the transaction was processed. I have attached the receipt showing proof of payment.",
        "I am pleading not guilty because I paid for parking using the mobile app at the time of parking. The ticket was issued either just before or right after the payment was confirmed. I've included the receipt to show this.",
        "I received a parking ticket even though I had paid using the parking app. The ticket was likely issued within a very short window before the payment was processed. I've attached the app receipt showing the payment time as proof."
    ])
    
    form_data = {
        'ticket_number': ticket_number,
        'first_name': profile.get('first_name', ''),
        'last_name': profile.get('last_name', ''),
        'license': profile.get('license', ''),
        'address': profile.get('address', ''),
        'city': profile.get('city', ''),
        'postal_code': profile.get('postal_code', ''),
        'email': profile.get('email', ''),
        'explanation': explanation
    }
    
    return render_template('fight_ticket.html', 
                         form_data=form_data, 
                         has_selenium_support=HAS_SELENIUM_SUPPORT)
# --- SELENIUM ROUTES ---
if HAS_SELENIUM_SUPPORT:
    @app.route('/fight_ticket_selenium', methods=['POST'])
    def fight_ticket_selenium():
        """Local-only Selenium automation for Montreal form filling"""
        print(f"🤖 Selenium route called - starting automation...")
        
        # Security check: only allow local requests
        if not is_local_request():
            print(f"❌ Access denied from {request.remote_addr}")
            abort(403, "Selenium automation only available for local requests")
        
        print(f"✅ Local request verified from {request.remote_addr}")
        
        try:
            # Handle both form data and JSON data
            if request.content_type == 'application/json':
                data = request.get_json(force=True) or {}
                ticket_number = data.get('ticket_number')
            else:
                data = request.form.to_dict()
                ticket_number = request.form.get('ticket_number')
            
            if not ticket_number or len(ticket_number) != 9 or not ticket_number.isdigit():
                return jsonify(ok=False, error="Valid 9-digit ticket number required"), 400
            
            profile = load_profile()
            if not profile:
                return jsonify(ok=False, error="Profile not found. Please set up your profile first."), 400
            
            # Set up Chrome options for local development
            options = Options()
            options.add_argument('--start-maximized')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Add SSL and connectivity options
            options.add_argument('--ignore-certificate-errors')
            options.add_argument('--ignore-ssl-errors')
            options.add_argument('--allow-running-insecure-content')
            options.add_argument('--disable-web-security')
            options.add_argument('--disable-features=VizDisplayCompositor')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            # Set up WebDriver
            print("🛠️ Setting up Chrome WebDriver...")
            driver_path = os.getenv('CHROMEDRIVER_PATH', r"C:\Users\ADMIN\Desktop\chromedriver.exe")
            
            try:
                if USE_WEBDRIVER_MANAGER:
                    # Use webdriver-manager for automatic ChromeDriver management
                    print("🔄 Downloading/updating ChromeDriver...")
                    service = Service(ChromeDriverManager().install())
                    print(f"🤖 Using WebDriver Manager for Chrome")
                elif os.path.exists(driver_path):
                    # Use specified driver path
                    service = Service(driver_path)
                    print(f"🤖 Using ChromeDriver at: {driver_path}")
                else:
                    # Try system PATH
                    service = Service()
                    print(f"🤖 Using ChromeDriver from system PATH")
                
                print("🌐 Starting Chrome browser...")
                driver = webdriver.Chrome(service=service, options=options)
                active_drivers.append(driver)
                wait = WebDriverWait(driver, 20)
                print("✅ Chrome browser started successfully")
                
            except Exception as webdriver_error:
                error_msg = str(webdriver_error)
                print(f"❌ WebDriver initialization failed: {error_msg}")
                
                # Provide helpful error messages
                if "chromedriver" in error_msg.lower():
                    return jsonify(ok=False, error="ChromeDriver not found. Please install Chrome browser or check ChromeDriver path."), 500
                elif "chrome" in error_msg.lower():
                    return jsonify(ok=False, error="Chrome browser not found. Please install Google Chrome."), 500
                else:
                    return jsonify(ok=False, error=f"Failed to start browser: {error_msg}"), 500
            
            try:
                print(f"🌐 Opening Montreal dispute page...")
                
                # Try to access the website with retries
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        driver.get('https://services.montreal.ca/plaidoyer/rechercher/en')
                        # Wait for page to load
                        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                        print(f"✅ Successfully loaded Montreal website (attempt {attempt + 1})")
                        break
                    except Exception as e:
                        print(f"⚠️ Attempt {attempt + 1} failed: {e}")
                        if attempt == max_retries - 1:
                            raise Exception(f"Could not access Montreal website after {max_retries} attempts. Check your internet connection.")
                        time.sleep(2)
                
                # Handle potential cookie banner
                try:
                    cookie_accept = wait.until(EC.element_to_be_clickable((By.ID, 'onetrust-accept-btn-handler')))
                    cookie_accept.click()
                    print("✅ Accepted cookie banner")
                except Exception:
                    pass  # No cookie banner or different selector
                
                # Step 1: Enter ticket number and search
                print(f"🔍 Searching for ticket {ticket_number}...")
                ticket_input = wait.until(EC.presence_of_element_located((By.ID, 'searchTxtStatementNo')))
                ticket_input.clear()
                ticket_input.send_keys(ticket_number)
                
                search_btn = wait.until(EC.element_to_be_clickable((By.ID, 'searchBtnSubmit')))
                search_btn.click()
                
                # Handle potential "Continue" or "Next" button after search
                try:
                    import time
                    time.sleep(2)  # Wait for potential redirect/loading
                    continue_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(normalize-space(), 'Continue') or contains(normalize-space(), 'Next') or contains(normalize-space(), 'Continuer')]")))
                    continue_btn.click()
                    print("✅ Clicked Continue button")
                except Exception:
                    pass  # No continue button needed
                
                # Step 2: Select "person whose name appears" (value='1')
                print("👤 Selecting person type...")
                try:
                    who_dropdown = wait.until(EC.presence_of_element_located((By.ID, 'who')))
                    who_dropdown.click()
                    time.sleep(0.5)
                    option = who_dropdown.find_element(By.CSS_SELECTOR, "option[value='1']")
                    option.click()
                    print("✅ Selected 'person whose name appears'")
                except Exception as e:
                    print(f"⚠️ Could not select person type: {e}")
                
                # Helper function to fill form fields safely
                def fill_field(field_id, value):
                    if not value:
                        return False
                    try:
                        element = wait.until(EC.presence_of_element_located((By.ID, field_id)))
                        element.clear()
                        element.send_keys(str(value))
                        return True
                    except Exception as e:
                        print(f"⚠️ Could not fill {field_id}: {e}")
                        return False
                
                # Step 3: Fill personal information
                print("📝 Filling personal information...")
                filled_fields = 0
                
                fields = [
                    ('firstName', data.get('first_name') or profile.get('first_name')),
                    ('lastName', data.get('last_name') or profile.get('last_name')),
                    ('licenceNumber', data.get('license') or profile.get('license')),
                    ('address', data.get('address') or profile.get('address')),
                    ('city', data.get('city') or profile.get('city')),
                    ('postalCode', data.get('postal_code') or profile.get('postal_code')),
                    ('email', data.get('email') or profile.get('email')),
                    ('confEmail', data.get('email') or profile.get('email'))
                ]
                
                for field_id, value in fields:
                    if fill_field(field_id, value):
                        filled_fields += 1
                
                # Step 4: Fill explanation
                explanation_text = data.get('explanation')
                if not explanation_text:
                    messages = [
                        "I had paid for parking through the app, but the officer issued the ticket just a few minutes before the transaction was processed. I have attached the receipt showing proof of payment.",
                        "I am pleading not guilty because I paid for parking using the mobile app at the time of parking. The ticket was issued either just before or right after the payment was confirmed. I've included the receipt to show this.",
                        "I received a parking ticket even though I had paid using the parking app. The ticket was likely issued within a very short window before the payment was processed. I've attached the app receipt showing the payment time as proof."
                    ]
                    explanation_text = random.choice(messages)
                
                if fill_field('explanation', explanation_text):
                    filled_fields += 1
                    print("✅ Added explanation")
                
                # Final wait for everything to settle
                time.sleep(1)
                
                print(f"✅ Successfully filled {filled_fields} fields for ticket {ticket_number}")
                print("🖥️ Chrome window is open - review the information and submit when ready")
                
                # DO NOT quit the driver - let user control the browser
                return jsonify({
                    'ok': True,
                    'message': f'Chrome opened and filled {filled_fields} fields for ticket #{ticket_number}. Review and submit manually.',
                    'ticket_number': ticket_number,
                    'fields_filled': filled_fields
                })
                
            except Exception as selenium_error:
                print(f"❌ Selenium error: {selenium_error}")
                return jsonify(ok=False, error=f"Automation error: {str(selenium_error)}"), 500
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"❌ General error: {e}")
            print(f"Full traceback:\n{error_details}")
            return jsonify(ok=False, error=f"Selenium failed: {str(e)}", details=error_details), 500

else:
    # Selenium is disabled - provide fallback route
    @app.route('/fight_ticket_selenium', methods=['POST'])
    def fight_ticket_selenium_disabled():
        import os
        debug_info = {
            'ENABLE_SELENIUM': os.getenv('ENABLE_SELENIUM'),
            'VERCEL': os.getenv('VERCEL'),
            'HAS_SELENIUM_SUPPORT': HAS_SELENIUM_SUPPORT,
            'reason': 'Selenium is disabled in this environment'
        }
        print(f"🚫 Selenium disabled. Debug info: {debug_info}")
        return jsonify(
            ok=False, 
            error="Selenium automation is disabled in this environment. Use the client-side options instead.",
            debug=debug_info
        ), 501

@app.route('/debug_selenium')
def debug_selenium():
    """Debug route to check Selenium configuration"""
    import os
    debug_info = {
        'ENABLE_SELENIUM': os.getenv('ENABLE_SELENIUM'),
        'VERCEL': os.getenv('VERCEL'), 
        'HAS_SELENIUM_SUPPORT': HAS_SELENIUM_SUPPORT,
        'USE_WEBDRIVER_MANAGER': globals().get('USE_WEBDRIVER_MANAGER', 'Not set'),
        'selenium_route_active': HAS_SELENIUM_SUPPORT
    }
    return jsonify(debug_info)

@app.route('/fight_ticket', methods=['GET', 'POST'])
def fight_ticket():
    if request.method == 'POST':
        # Try Selenium automation first
        return fight_ticket_selenium()
    else:
        # GET request - redirect to Montreal site
        ticket_number = request.args.get("ticket")
        return redirect(f"https://services.montreal.ca/plaidoyer/rechercher/en?ticket={ticket_number}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)


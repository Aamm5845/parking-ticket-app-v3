import os
import json
import random
import re
import csv
import ssl
from datetime import datetime, timedelta
from io import BytesIO
from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify, make_response, flash
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


# --- PROFILE HELPERS ---
def save_profile(data):
    try:
        with open(PROFILE_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Error saving profile: {e}")

def load_profile():
    try:
        if os.path.exists(PROFILE_FILE):
            with open(PROFILE_FILE, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Error loading profile: {e}")
        return {}

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
    if not profile:
        return redirect(url_for('setup_profile'))
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
    final_pdf_in_memory = BytesIO()
    output.write(final_pdf_in_memory)
    final_pdf_in_memory.seek(0)

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
        
        # Try local OCR fallback
        try:
            from local_ocr import extract_ticket_info_local, simple_ocr_fallback
            
            # Reset file pointer
            file.seek(0)
            content = file.read()
            
            # Try local OCR first
            result = extract_ticket_info_local(content)
            if "error" not in result:
                return jsonify(
                    success=True,
                    ticket_number=result.get("ticket_number", ""),
                    space=result.get("space", ""),
                    date=result.get("date", ""),
                    start_time=result.get("start_time", ""),
                    message="Used local OCR (Tesseract)"
                )
            
            # If local OCR fails, use mock data for development
            fallback_result = simple_ocr_fallback(content)
            return jsonify(
                success=True,
                ticket_number=fallback_result["ticket_number"],
                space=fallback_result["space"],
                date=fallback_result["date"],
                start_time=fallback_result["start_time"],
                message="OCR unavailable - using sample data for testing"
            )
            
        except Exception as fallback_error:
            print(f"Fallback OCR also failed: {fallback_error}")
            return jsonify(success=False, message=f"OCR failed: {str(e)}. Try manual entry."), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

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
@app.route('/fight_ticket_selenium', methods=['POST'])
def fight_ticket_selenium():
    """Server-side Selenium automation for Montreal form filling"""
    try:
        ticket_number = request.form.get('ticket_number')
        if not ticket_number or len(ticket_number) != 9 or not ticket_number.isdigit():
            return jsonify(success=False, message="Valid 9-digit ticket number required"), 400
        
        profile = load_profile()
        if not profile:
            return jsonify(success=False, message="Profile not found. Please set up your profile first."), 400
        
        # Import Selenium here to avoid issues on platforms where it's not available
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options
        import time
        
        # Set up Chrome options for Heroku environment
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--remote-debugging-port=9222")
        
        # Heroku-specific Chrome setup
        if os.environ.get("DYNO"):  # Running on Heroku
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--no-first-run")
            chrome_options.add_argument("--disable-default-apps")
            chrome_options.add_argument("--single-process")
            chrome_options.binary_location = "/app/.chrome-for-testing/chrome-linux64/chrome"
            driver = webdriver.Chrome(options=chrome_options)
        else:
            # Local development setup
            driver_path = r"C:\Users\ADMIN\Desktop\chromedriver.exe"
            if os.path.exists(driver_path):
                service = Service(driver_path)
                driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                # Fallback to system PATH chromedriver
                driver = webdriver.Chrome(options=chrome_options)
        
        try:
            driver.maximize_window()
            
            # Load Montreal ticket page
            driver.get("https://services.montreal.ca/plaidoyer/rechercher/en")
            wait = WebDriverWait(driver, 20)
            
            # Step 1: Enter ticket number and search
            ticket_input = wait.until(EC.presence_of_element_located((By.ID, "searchTxtStatementNo")))
            ticket_input.send_keys(ticket_number)
            
            search_btn = wait.until(EC.element_to_be_clickable((By.ID, "searchBtnSubmit")))
            search_btn.click()
            
            # Step 2: Select "person whose name appears"
            who_dropdown = wait.until(EC.presence_of_element_located((By.ID, "who")))
            who_dropdown.click()
            time.sleep(0.5)
            option = who_dropdown.find_element(By.CSS_SELECTOR, "option[value='1']")
            option.click()
            
            # Step 3: Fill personal information
            wait.until(EC.presence_of_element_located((By.ID, "firstName"))).send_keys(profile.get('first_name', ''))
            driver.find_element(By.ID, "lastName").send_keys(profile.get('last_name', ''))
            driver.find_element(By.ID, "licenceNumber").send_keys(profile.get('license', ''))
            driver.find_element(By.ID, "address").send_keys(profile.get('address', ''))
            driver.find_element(By.ID, "city").send_keys(profile.get('city', ''))
            driver.find_element(By.ID, "postalCode").send_keys(profile.get('postal_code', ''))
            driver.find_element(By.ID, "email").send_keys(profile.get('email', ''))
            driver.find_element(By.ID, "confEmail").send_keys(profile.get('email', ''))
            
            # Step 4: Add explanation
            messages = [
                "I had paid for parking through the app, but the officer issued the ticket just a few minutes before the transaction was processed. I have attached the receipt showing proof of payment.",
                "I am pleading not guilty because I paid for parking using the mobile app at the time of parking. The ticket was issued either just before or right after the payment was confirmed. I've included the receipt to show this.",
                "I received a parking ticket even though I had paid using the parking app. The ticket was likely issued within a very short window before the payment was processed. I've attached the app receipt showing the payment time as proof."
            ]
            chosen_message = random.choice(messages)
            explanation_field = driver.find_element(By.ID, "explanation")
            explanation_field.send_keys(chosen_message)
            
            # Give a moment for everything to settle
            time.sleep(2)
            
            # Keep browser open for user to review and submit
            # Don't quit the driver - let user control it
            print(f"✅ Form filled successfully for ticket {ticket_number}")
            print("Browser will remain open for user to review and submit")
            
            return jsonify({
                'success': True, 
                'message': f"Montreal form opened and filled successfully for ticket #{ticket_number}! The browser window is now open - review the information and submit when ready.",
                'ticket_number': ticket_number
            })
            
        except Exception as selenium_error:
            # Don't automatically close browser on errors - user might want to see what happened
            print(f"Selenium error occurred: {selenium_error}")
            raise selenium_error
            
    except ImportError:
        return jsonify(success=False, message="Selenium not available on this platform. Please use manual form filling."), 500
    except Exception as e:
        print(f"Selenium automation error: {e}")
        return jsonify(success=False, message=f"Automation failed: {str(e)}"), 500

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


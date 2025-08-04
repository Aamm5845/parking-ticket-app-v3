from flask import Flask, render_template, request, redirect, url_for, send_file, session, jsonify, make_response, flash
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
from datetime import datetime, timedelta
import random
import csv
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
import re
from io import BytesIO
from google.cloud import vision
from google.oauth2 import service_account

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'a_very_secret_key_for_development')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

PROFILE_PATH = 'profile.json'
CSV_PATH = 'static/Mobicite_Placeholder_Locations.csv'
TEMPLATE_PDF = 'static/base_template.pdf'

# Load profiles or create empty
if os.path.exists(PROFILE_PATH):
    with open(PROFILE_PATH, 'r') as f:
        try:
            profiles = json.load(f)
        except json.JSONDecodeError:
            profiles = {}
else:
    profiles = {}

# Initialize Google Cloud Vision client
try:
    credentials_json = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_JSON')
    if credentials_json:
        credentials = service_account.Credentials.from_service_account_info(json.loads(credentials_json))
        client = vision.ImageAnnotatorClient(credentials=credentials)
    else:
        client = None
except Exception as e:
    client = None
    print(f"Warning: Google Cloud Vision client could not be initialized. Error: {e}")

# --- Core App and PWA Routes ---
@app.route('/')
def index():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    
    profile = profiles.get(session.get('user_email'))
    if not profile:
        session.pop('user_email', None)
        return redirect(url_for('login'))
        
    return render_template('index.html', profile=profile)

@app.route('/sw.js')
def service_worker():
    response = make_response(send_file('sw.js'))
    response.headers['Content-Type'] = 'application/javascript'
    return response

# --- AUTHENTICATION SYSTEM ---
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password:
            flash('Email and password are required.')
            return redirect(url_for('signup'))
        if email in profiles:
            flash('Email address already exists. Please log in.')
            return redirect(url_for('login'))
        
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        
        new_user = {
            'first_name': request.form.get('first_name', ''),
            'last_name': request.form.get('last_name', ''),
            'license': request.form.get('license', ''),
            'address': request.form.get('address', ''),
            'city': request.form.get('city', ''),
            'province': request.form.get('province', 'Québec'),
            'postal_code': request.form.get('postal_code', ''),
            'country': request.form.get('country', 'Canada'),
            'email': email,
            'password_hash': password_hash
        }
        
        profiles[email] = new_user
        with open(PROFILE_PATH, 'w') as f:
            json.dump(profiles, f, indent=2)
        
        session.permanent = True
        session['user_email'] = email
        return redirect(url_for('index'))
        
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = profiles.get(email)

        if not user or not check_password_hash(user.get('password_hash', ''), password):
            flash('Please check your login details and try again.')
            return redirect(url_for('login'))
        
        session['user_email'] = email
        session.permanent = remember
        
        return redirect(url_for('index'))
        
    return render_template('login.html')

@app.route('/signout')
def signout():
    session.pop('user_email', None)
    return redirect(url_for('login'))

# --- Profile and Plea Helper Routes ---
@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    
    user_email = session['user_email']
    profile = profiles.get(user_email)

    if not profile:
        return redirect(url_for('login'))

    if request.method == 'POST':
        profile['first_name'] = request.form.get('first_name', profile.get('first_name'))
        profile['last_name'] = request.form.get('last_name', profile.get('last_name'))
        profile['license'] = request.form.get('license', profile.get('license'))
        profile['address'] = request.form.get('address', profile.get('address'))
        profile['city'] = request.form.get('city', profile.get('city'))
        profile['province'] = request.form.get('province', profile.get('province'))
        profile['postal_code'] = request.form.get('postal_code', profile.get('postal_code'))
        profile['country'] = request.form.get('country', profile.get('country'))
        
        profiles[user_email] = profile
        with open(PROFILE_PATH, 'w') as f:
            json.dump(profiles, f, indent=2)
        
        flash('Profile updated successfully!')
        return redirect(url_for('index'))

    return render_template('edit_profile.html', profile=profile)

@app.route('/plea-helper/<ticket_number>')
def plea_helper(ticket_number):
    if 'user_email' not in session:
        return redirect(url_for('login'))
    
    profile = profiles.get(session['user_email'])
    pdf_filename = session.get('current_pdf_filename')
    
    montreal_url = f"https://services.montreal.ca/plaidoyer/rechercher/en?statement={ticket_number}"
    plea_text = "I plead not guilty. The parking meter was paid for the entire duration that my vehicle was parked at this location."
    download_url = url_for('download_pdf', filename=pdf_filename) if pdf_filename else None

    return render_template('plea_helper.html', profile=profile, montreal_url=montreal_url, plea_text=plea_text, ticket_number=ticket_number, download_url=download_url)

# --- PDF and OCR Routes ---
@app.route('/generate-and-get-link', methods=['POST'])
def generate_and_get_link():
    data = request.form
    ticket_number = data.get('ticket_number')

    if not ticket_number or not ticket_number.isdigit() or len(ticket_number) != 9:
        return jsonify(success=False, message="Ticket number must be exactly 9 digits."), 400

    # --- FULL PDF GENERATION LOGIC ---
    transaction = ' 00003' + ''.join([str(random.randint(0, 9)) for _ in range(5)])
    reference_number = ' ' + ''.join([str(random.randint(0, 9)) for _ in range(18)])
    auth_code = ' ' + ''.join([str(random.randint(0, 9)) for _ in range(6)])
    response_code = ' 027'
    space_raw = data.get('space', '')
    space_cleaned = re.sub(r'[^A-Za-z0-9]', '', space_raw)
    space_caps = ''.join([char.upper() if char.isalpha() else char for char in space_cleaned])
    date_str = data.get('date')
    time_str = data.get('start_time')
    if not date_str or not time_str:
        return jsonify(success=False, message="Date and Start Time are required."), 400
    date_obj = datetime.strptime(date_str + ' ' + time_str, '%Y-%m-%d %H:%M')
    offset_minutes = random.randint(1, 2)
    adjusted_date_obj = date_obj + timedelta(minutes=offset_minutes)
    start_time = adjusted_date_obj.strftime('%Y-%m-%d, %H:%M')
    end_time = (adjusted_date_obj + timedelta(minutes=10)).strftime('%Y-%m-%d, %H:%M')
    date_line = f" {adjusted_date_obj.strftime('%a, %b %d, %Y at %I:%M %p')}"
    transaction_datetime = ' ' + adjusted_date_obj.strftime('%Y-%m-%d, %H:%M')
    values = {
        'Transaction number': transaction, 'Authorization code': auth_code, 'Response code': response_code,
        'Space number': ' ' + space_caps, 'Start of session': ' ' + start_time, 'End of session': ' ' + end_time,
        'Top date line': date_line, 'Reference number': reference_number
    }
    
    pdf_filename = f"Tickety_Receipt_{ticket_number}_{random.randint(1000,9999)}.pdf"
    pdf_path = os.path.join('static', pdf_filename)
    
    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=letter)
    with open(CSV_PATH, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            field = row['field']
            text = values.get(field, row['text'])
            x_pt = float(row['x_in']) * 72
            y_pt = (11 - (float(row['y_in']) + 0.1584)) * 72
            c.setFont("Helvetica", 11)
            c.drawString(x_pt, y_pt, text)
    ref_x = 2.0836 * 72
    ref_y = (11 - (6.6827 + 0.1584)) * 72
    c.drawString(ref_x, ref_y, reference_number)
    tx_x = 1.9515 * 72
    tx_y = (11 - (4.8789 + 0.1584)) * 72
    c.drawString(tx_x, tx_y, transaction_datetime)
    c.save()
    packet.seek(0)
    
    output = PdfWriter()
    background = PdfReader(TEMPLATE_PDF)
    overlay = PdfReader(packet)
    page = background.pages[0]
    page.merge_page(overlay.pages[0])
    output.add_page(page)
    with open(pdf_path, 'wb') as f:
        output.write(f)
    
    session['current_pdf_filename'] = pdf_filename
    
    return jsonify(success=True, plea_helper_url=url_for('plea_helper', ticket_number=ticket_number))

@app.route('/download/<filename>')
def download_pdf(filename):
    return send_file(os.path.join('static', filename), as_attachment=True)

@app.route('/scan-ticket', methods=['POST'])
def scan_ticket():
    if not client:
        return jsonify(success=False, message="OCR client not configured."), 500
    if 'ticket_image' not in request.files:
        return jsonify(success=False, message="No image file provided."), 400
    file = request.files['ticket_image']
    if file.filename == '':
        return jsonify(success=False, message="No file selected."), 400
    try:
        content = file.read()
        image = vision.Image(content=content)
        response = client.document_text_detection(image=image)
        raw_text = response.full_text_annotation.text
        
        ticket_number, space_number, extracted_date, extracted_time = "", "", "", ""

        ticket_match = re.search(r'\b(\d{3})\s*(\d{3})\s*(\d{3})\b', raw_text)
        if ticket_match:
            ticket_number = "".join(ticket_match.groups())
        
        space_match = re.search(r'(PL\d+)', raw_text, re.IGNORECASE)
        if space_match:
            space_number = space_match.group(1).upper()
        
        date_time_match = re.search(r'au\s+(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})', raw_text, re.IGNORECASE) or \
                          re.search(r'Date\s+de\s+signification:\s*(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})', raw_text, re.IGNORECASE)
        
        if date_time_match:
            extracted_date, extracted_time = date_time_match.groups()
        
        return jsonify(
            success=True, ticket_number=ticket_number, space=space_number,
            date=extracted_date, start_time=extracted_time
        )
    except Exception as e:
        return jsonify(success=False, message=f"Error processing image: {str(e)}"), 500

# --- Main Execution ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)



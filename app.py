from flask import Flask, render_template, request, redirect, url_for, send_file, session, jsonify
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

# IMPORTS FOR GOOGLE CLOUD VISION
from google.cloud import vision
from google.oauth2 import service_account
from google.api_core.client_options import ClientOptions

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key_here')

PROFILE_PATH = 'profile.json'
TEMPLATE_PDF = 'static/base_template.pdf'
FILLED_PDF = 'static/output.pdf'
CSV_PATH = 'static/Mobicite_Placeholder_Locations.csv'

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
        print("Warning: GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable is not set. OCR features will not work.")
except Exception as e:
    client = None
    print(f"Warning: Google Cloud Vision client could not be initialized. OCR features will not work. Error: {e}")


# --- User & Profile Routes (Unchanged) ---
@app.route('/')
def index():
    profile = session.get('profile')
    return render_template('index.html', profile=profile)

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        profile = {
            'first_name': request.form['first_name'],
            'last_name': request.form['last_name'],
            'address': request.form['address'],
            'email': request.form['email'],
            'license': request.form['license']
        }
        key = profile['email']
        profiles[key] = profile
        with open(PROFILE_PATH, 'w') as f:
            json.dump(profiles, f, indent=2)
        session['profile'] = profile
        return redirect(url_for('index'))
    return render_template('signin.html')

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    profile = session.get('profile')
    if not profile:
        return redirect(url_for('signin'))
    if request.method == 'POST':
        # ... (profile update logic)
        session['profile'] = profile
        return redirect(url_for('index'))
    return render_template('edit_profile.html', profile=profile)

@app.route('/signout')
def signout():
    session.pop('profile', None)
    return redirect(url_for('index'))

# --- PDF Generation and Download Routes ---

@app.route('/generate-and-get-link', methods=['POST'])
def generate_and_get_link():
    """
    Generates a PDF and returns JSON with a download link and a pre-filled link for the Montreal portal.
    """
    data = request.form
    # BUG FIX: Use .get() for safer data retrieval
    ticket_number = data.get('ticket_number')

    if not ticket_number or not ticket_number.isdigit() or len(ticket_number) != 9:
        return jsonify(success=False, message="Ticket number must be exactly 9 digits."), 400

    # --- PDF generation logic (no changes here) ---
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
    packet_path = 'static/temp.pdf'
    c = canvas.Canvas(packet_path, pagesize=letter)
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
    output = PdfWriter()
    background = PdfReader(TEMPLATE_PDF)
    overlay = PdfReader(packet_path)
    page = background.pages[0]
    page.merge_page(overlay.pages[0])
    output.add_page(page)
    with open(FILLED_PDF, 'wb') as f:
        output.write(f)
    # --- End of PDF logic ---

    # Create the special pre-filled URL for the Montreal portal
    montreal_url = f"https://services.montreal.ca/plaidoyer/rechercher/en?numeroConstat={ticket_number}"

    return jsonify(
        success=True,
        message="PDF generated successfully!",
        download_url=url_for('download_pdf'),
        montreal_url=montreal_url
    )

@app.route('/download-pdf')
def download_pdf():
    """Serves the generated PDF for downloading."""
    return send_file(FILLED_PDF, as_attachment=True, download_name=f"Tickety_Receipt.pdf")


# --- OCR Route (with added debugging) ---
@app.route('/scan-ticket', methods=['POST'])
def scan_ticket():
    """Handles an image upload, performs OCR, and returns a JSON response."""
    # DEBUG: Confirm the route was triggered
    print("--- Starting scan-ticket route ---")

    if not client:
        print("Error: Google Cloud Vision client is not configured.")
        return jsonify(success=False, message="Google Cloud Vision API client is not configured."), 500
    if 'ticket_image' not in request.files:
        print("Error: No image file provided in request.")
        return jsonify(success=False, message="No image file provided."), 400
    file = request.files['ticket_image']
    if file.filename == '':
        print("Error: No file selected by user.")
        return jsonify(success=False, message="No file selected."), 400
    if file:
        try:
            # DEBUG: Confirm file processing is starting
            print("Processing image file...")
            content = file.read()
            image = vision.Image(content=content)

            # DEBUG: Confirm API call is being made
            print("Sending image to Google Cloud Vision API...")
            response = client.document_text_detection(image=image)
            raw_text = response.full_text_annotation.text
            
            # DEBUG: Print the most important info - the raw text from the API
            print(f"--- Raw OCR Text from Google Cloud Vision:\n{raw_text}")

            # --- OCR TEXT PARSING LOGIC ---
            ticket_number = ""
            space_number = ""
            extracted_date = ""
            extracted_time = ""

            ticket_match = re.search(r'\b(\d{3})\s*(\d{3})\s*(\d{3})\b', raw_text)
            if ticket_match:
                ticket_number = ticket_match.group(1) + ticket_match.group(2) + ticket_match.group(3)

            space_match = re.search(r'(PL\d+)', raw_text, re.IGNORECASE)
            if space_match:
                space_number = space_match.group(1).upper()

            date_time_match = re.search(r'to\s+(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})', raw_text, re.IGNORECASE)
            if not date_time_match:
                date_time_match = re.search(r'Date\s+de\s+signification:\s*(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})', raw_text, re.IGNORECASE)

            if date_time_match:
                extracted_date = date_time_match.group(1)
                extracted_time = date_time_match.group(2)

            # DEBUG: Show what was actually extracted by the code
            print(f"Extracted Data: Ticket={ticket_number}, Space={space_number}, Date={extracted_date}, Time={extracted_time}")

            # DEBUG: Confirm successful completion
            print("OCR successful. Returning JSON data.")
            return jsonify(
                success=True, ticket_number=ticket_number, space=space_number,
                date=extracted_date, start_time=extracted_time
            )
        except Exception as e:
            # DEBUG: Print any errors that occur during the process
            print(f"An error occurred during OCR processing: {e}")
            return jsonify(success=False, message=f"Error processing image with API: {str(e)}"), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

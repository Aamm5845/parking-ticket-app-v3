import os
import json
import random
import re
import csv
from datetime import datetime, timedelta
from io import BytesIO
from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify, make_response, flash
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from google.cloud import vision
from google.oauth2 import service_account
import resend

# --- APP SETUP ---
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'a_very_secret_key_for_development')

# Configure Resend for Emails
resend.api_key = os.environ.get("RESEND_API_KEY")

# File paths
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(APP_ROOT, 'static', 'Mobicite_Placeholder_Locations.csv')
TEMPLATE_PDF = os.path.join(APP_ROOT, 'static', 'base_template.pdf')

# ✅ FIXED: Use /tmp on Vercel, local folder when testing
PROFILE_FILE = os.path.join('/tmp', 'profile.json') if os.environ.get("VERCEL") else os.path.join(APP_ROOT, 'profile.json')

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
    print(f"Warning: Google Vision client not initialized: {e}")

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

    # --- ALWAYS SEND EMAIL WITH PDF + BUTTON ---
    try:
        user_profile = load_profile()
        if user_profile and user_profile.get('email'):
            autofill_url = generate_autofill_url(user_profile, data)

            email_params = {
                "from": "Tickety <onboarding@resend.dev>",
                "to": [user_profile['email']],
                "subject": f"Your Parking Receipt for Ticket #{ticket_number}",
                "html": f"""
                <div style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
                    <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0px 2px 6px rgba(0,0,0,0.1);">
                        <h2 style="color: #333;">Hi {user_profile['first_name']},</h2>
                        <p>We've attached your parking receipt for ticket <strong>#{ticket_number}</strong>.</p>
                        <p style="margin-top: 20px;">
                            <a href="{autofill_url}" style="display: inline-block; background-color: #0070f3; color: white;
                            padding: 12px 18px; text-decoration: none; border-radius: 6px; font-size: 16px;">
                                🚗 Fight Your Ticket
                            </a>
                        </p>
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
            resend.Emails.send(email_params)
    except Exception as e:
        print(f"Email error: {e}")
        flash('PDF generated, but email sending failed.', 'error')

    # Always return PDF to download too
    final_pdf_in_memory.seek(0)
    return send_file(
        final_pdf_in_memory,
        as_attachment=True,
        download_name=f'Tickety_Receipt_{ticket_number}.pdf',
        mimetype='application/pdf'
    )

@app.route('/plea-helper')
def plea_helper():
    profile = load_profile()
    if not profile:
        return redirect(url_for('setup_profile'))
    ticket_number = request.args.get('ticket_number', '')
    montreal_url = f"https://services.montreal.ca/plaidoyer/rechercher/en?statement={ticket_number}"
    plea_text = "I plead not guilty. The parking meter was paid for the entire duration that my vehicle was parked at this location."
    return render_template('plea_helper.html', profile=profile, montreal_url=montreal_url, plea_text=plea_text, ticket_number=ticket_number)

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
        date_time_match = (
            re.search(r'au\s+(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})', raw_text, re.IGNORECASE)
            or re.search(r'Date\s+de\s+signification:\s*(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})', raw_text, re.IGNORECASE)
            or re.search(r'\b(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})\b', raw_text)
        )
        if date_time_match:
            extracted_date, extracted_time = date_time_match.groups()

        return jsonify(success=True, ticket_number=ticket_number, space=space_number, date=extracted_date, start_time=extracted_time)
    except Exception as e:
        return jsonify(success=False, message=f"Error processing image: {str(e)}"), 500

@app.route('/test-env')
def test_env():
    test_value = os.environ.get("TEST_VAR", "---VARIABLE NOT FOUND---")
    return f"<h1>The value of TEST_VAR is: {test_value}</h1>"

# --- MAIN ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

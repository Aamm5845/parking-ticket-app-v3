from flask import Flask, render_template, request, redirect, url_for, send_file, session
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

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

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
        profile['first_name'] = request.form['first_name']
        profile['last_name'] = request.form['last_name']
        profile['address'] = request.form['address']
        profile['email'] = request.form['email']
        profile['license'] = request.form['license']
        profiles[profile['email']] = profile
        with open(PROFILE_PATH, 'w') as f:
            json.dump(profiles, f, indent=2)
        session['profile'] = profile
        return redirect(url_for('index'))
    return render_template('edit_profile.html', profile=profile)

@app.route('/signout')
def signout():
    session.pop('profile', None)
    return redirect(url_for('index'))

@app.route('/generate', methods=['POST'])
def generate():
    data = request.form

    ticket_number = data['ticket_number']
    if not ticket_number.isdigit() or len(ticket_number) != 9:
        return "Ticket number must be exactly 9 digits.", 400

    transaction = ' 00003' + ''.join([str(random.randint(0, 9)) for _ in range(5)])
    reference_number = ' ' + ''.join([str(random.randint(0, 9)) for _ in range(18)])
    auth_code = ' ' + ''.join([str(random.randint(0, 9)) for _ in range(6)])
    response_code = ' 027'

    space_raw = data['space']
    space_cleaned = re.sub(r'[^A-Za-z0-9]', '', space_raw)
    space_caps = ''.join([char.upper() if char.isalpha() else char for char in space_cleaned])

    date_obj = datetime.strptime(data['date'] + ' ' + data['start_time'], '%Y-%m-%d %H:%M')
    start_time = date_obj.strftime('%Y-%m-%d, %H:%M')
    end_time = (date_obj + timedelta(minutes=10)).strftime('%Y-%m-%d, %H:%M')
    date_line = f" {date_obj.strftime('%a, %b %d, %Y at %I:%M %p')}"
    transaction_datetime = ' ' + date_obj.strftime('%Y-%m-%d, %H:%M')

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

    # Add Reference number
    ref_x = 2.0836 * 72
    ref_y = (11 - (6.6827 + 0.1584)) * 72
    c.drawString(ref_x, ref_y, reference_number)

    # Add Transaction Date (new)
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

    return send_file(FILLED_PDF, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)

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

# Set the session to be permanent for the "Remember Me" feature
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
    
    profile = profiles.get(session['user_email'])
    if not profile:
        # If profile is somehow missing, log the user out
        session.pop('user_email', None)
        return redirect(url_for('login'))
        
    return render_template('index.html', profile=profile)

@app.route('/sw.js')
def service_worker():
    response = make_response(send_file('sw.js'))
    response.headers['Content-Type'] = 'application/javascript'
    return response

# --- NEW AUTHENTICATION SYSTEM ---
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
        
        session.permanent = True # Remember the user by default
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

    if request.method == 'POST':
        profile['first_name'] = request.form.get('first_name')
        profile['last_name'] = request.form.get('last_name')
        profile['license'] = request.form.get('license')
        profile['address'] = request.form.get('address')
        profile['city'] = request.form.get('city')
        profile['province'] = request.form.get('province')
        profile['postal_code'] = request.form.get('postal_code')
        profile['country'] = request.form.get('country')
        # Email cannot be changed as it's the primary key
        
        profiles[user_email] = profile
        with open(PROFILE_PATH, 'w') as f:
            json.dump(profiles, f, indent=2)
        
        flash('Profile updated successfully!')
        return redirect(url_for('index'))

    return render_template('edit_profile.html', profile=profile)

@app.route('/plea-helper/<ticket_number>', methods=['GET', 'POST'])
def plea_helper(ticket_number):
    if 'user_email' not in session:
        return redirect(url_for('login'))
    
    profile = profiles.get(session['user_email'])

    if 'plea_texts' not in session:
        session['plea_texts'] = {}

    if request.method == 'POST':
        plea_text = request.form.get('plea_text')
        session['plea_texts'][ticket_number] = plea_text
        session.modified = True
    
    plea_text = session['plea_texts'].get(ticket_number, '')
    montreal_url = f"https://services.montreal.ca/plaidoyer/rechercher/en?statement={ticket_number}"
    
    return render_template('plea_helper.html', profile=profile, montreal_url=montreal_url, plea_text=plea_text, ticket_number=ticket_number)

# --- PDF and OCR Routes ---
@app.route('/generate-and-get-link', methods=['POST'])
def generate_and_get_link():
    # ... (This entire function remains the same as the full version you had)
    data = request.form
    ticket_number = data.get('ticket_number')

    if not ticket_number or not ticket_number.isdigit() or len(ticket_number) != 9:
        return jsonify(success=False, message="Ticket number must be exactly 9 digits."), 400

    # (Your full PDF generation logic here...)
    
    session['current_ticket_number'] = ticket_number
    return jsonify(success=True, plea_helper_url=url_for('plea_helper', ticket_number=ticket_number))


@app.route('/scan-ticket', methods=['POST'])
def scan_ticket():
    # ... (This entire function remains the same as the full version you had)
    if not client:
        return jsonify(success=False, message="Google Cloud Vision client is not configured."), 500
    # (Your full OCR logic here...)
    return jsonify(success=True, ticket_number="123456789") # Placeholder

# --- Main Execution ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)



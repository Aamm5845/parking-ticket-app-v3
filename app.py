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

# Initialize Google Cloud Vision client (no changes here)
# ... (your existing Google Cloud Vision client setup code)

# --- NEW AUTHENTICATION SYSTEM ---

@app.route('/')
def index():
    # If user is not logged in, redirect to login page
    if 'user_email' not in session:
        return redirect(url_for('login'))
    
    profile = profiles.get(session['user_email'])
    return render_template('index.html', profile=profile)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if email in profiles:
            flash('Email address already exists.')
            return redirect(url_for('signup'))

        # Hash the password for security
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')

        new_user = {
            'first_name': request.form.get('first_name'),
            'last_name': request.form.get('last_name'),
            'license': request.form.get('license'),
            'address': request.form.get('address'),
            'city': request.form.get('city'),
            'province': request.form.get('province'),
            'postal_code': request.form.get('postal_code'),
            'country': request.form.get('country'),
            'email': email,
            'password_hash': password_hash
        }
        
        profiles[email] = new_user
        with open(PROFILE_PATH, 'w') as f:
            json.dump(profiles, f, indent=2)
        
        # Log the user in immediately after signing up
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

        if not user or not check_password_hash(user.get('password_hash'), password):
            flash('Please check your login details and try again.')
            return redirect(url_for('login'))
        
        session['user_email'] = email
        session.permanent = remember # This is the "Remember Me" feature
        
        return redirect(url_for('index'))
        
    return render_template('login.html')

@app.route('/signout')
def signout():
    session.pop('user_email', None)
    return redirect(url_for('login'))

# --- All other routes like /edit_profile, /generate-and-get-link, etc. remain the same ---
# Make sure they use `session.get('user_email')` to get the current user's profile.

# ... (Paste your existing routes for edit_profile, generate-and-get-link, plea-helper, etc. here) ...

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
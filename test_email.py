#!/usr/bin/env python3
"""
Simple test script to verify email functionality
"""
import os
import ssl
import requests
import resend
from dotenv import load_dotenv

# Fix SSL certificate issues on Windows
try:
    import certifi
    os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
    os.environ['SSL_CERT_FILE'] = certifi.where()
except ImportError:
    # If certifi is not available, disable SSL verification (not recommended for production)
    ssl._create_default_https_context = ssl._create_unverified_context
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables
load_dotenv()

# Initialize Resend
resend.api_key = os.environ.get('RESEND_API_KEY')

print(f"API Key configured: {'Yes' if resend.api_key else 'No'}")
if resend.api_key:
    print(f"API Key (first 10 chars): {resend.api_key[:10]}...")

# Test sending a simple email
def test_email(to_email):
    try:
        print(f"\nTesting email to: {to_email}")
        
        email_params = {
            "from": "Tickety <onboarding@resend.dev>",
            "to": [to_email],
            "subject": "Tickety Test Email",
            "html": """
            <div style="font-family: Arial, sans-serif; padding: 20px;">
                <h2>Test Email from Tickety</h2>
                <p>This is a test email to verify the email functionality is working.</p>
                <p>If you received this, the email system is working correctly!</p>
            </div>
            """
        }
        
        response = resend.Emails.send(email_params)
        print(f"✅ Email sent successfully!")
        print(f"Response: {response}")
        return True
        
    except Exception as e:
        print(f"❌ Email failed: {e}")
        print(f"Error type: {type(e)}")
        return False

if __name__ == "__main__":
    print("=== Tickety Email Test ===")
    
    if not resend.api_key:
        print("❌ No RESEND_API_KEY found in .env file")
        print("Make sure you have a .env file with RESEND_API_KEY=your_key")
    else:
        email = input("Enter email address to test: ").strip()
        if email:
            test_email(email)
        else:
            print("No email address provided")

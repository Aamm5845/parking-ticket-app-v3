#!/usr/bin/env python3
import os
import ssl
import requests
from dotenv import load_dotenv

# Fix SSL certificate issues on Windows
try:
    import certifi
    os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
    os.environ['SSL_CERT_FILE'] = certifi.where()
    print("✅ Using certifi for SSL certificates")
except ImportError:
    print("⚠️ certifi not found, disabling SSL verification")
    ssl._create_default_https_context = ssl._create_unverified_context
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment
load_dotenv()

# Test with direct requests
def test_direct_email():
    api_key = os.environ.get('RESEND_API_KEY')
    if not api_key:
        print("❌ No API key found")
        return
        
    print(f"Using API key: {api_key[:10]}...")
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    data = {
        "from": "Tickety <onboarding@resend.dev>",
        "to": ["AAMM5845@GMAIL.COM"],
        "subject": "Test Email from Tickety",
        "html": "<h1>Test Email</h1><p>If you see this, email is working!</p>"
    }
    
    try:
        print("Sending direct HTTP request to Resend API...")
        response = requests.post(
            'https://api.resend.com/emails',
            headers=headers,
            json=data,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Email sent successfully!")
        else:
            print("❌ Email failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_direct_email()

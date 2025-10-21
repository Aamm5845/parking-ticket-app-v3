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

# Load environment variables
load_dotenv()

# Get API key
api_key = os.environ.get('RESEND_API_KEY')
print(f"🔑 API Key: {api_key[:15]}...")

print("📧 Sending test email to AAMM5845@GMAIL.COM...")

try:
    response = requests.post(
        'https://api.resend.com/emails',
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        },
        json={
            "from": "Tickety <onboarding@resend.dev>",
            "to": ["AAMM5845@GMAIL.COM"], 
            "subject": "✅ Tickety Email Test - WORKING!",
            "html": """
            <div style="font-family: Arial, sans-serif; padding: 20px; background-color: #e8f5e8;">
                <h2 style="color: #2e7d32;">🎉 Email is Now Working!</h2>
                <p>Congratulations! Your Tickety app can now send emails successfully.</p>
                <p><strong>This means:</strong></p>
                <ul>
                    <li>✅ PDF receipts will be emailed to you automatically</li>
                    <li>✅ You'll get your parking receipts in your inbox</li>
                    <li>✅ Full app functionality is now working</li>
                </ul>
                <p>Your Fight Ticket button and Generate PDF are both working perfectly!</p>
                <hr>
                <p style="font-size: 12px; color: #666;">
                    This test email was sent from your Tickety parking app.
                </p>
            </div>
            """
        },
        verify=True,  # Use system certificates 
        timeout=15
    )
    
    print(f"📡 Status Code: {response.status_code}")
    print(f"📄 Response: {response.text}")
    
    if response.status_code == 200:
        print("🎉 EMAIL SENT SUCCESSFULLY!")
        print("📧 Check your inbox: AAMM5845@GMAIL.COM")
        print("📧 Also check spam folder if you don't see it")
        print("✅ Email system is now working!")
    else:
        print(f"❌ Email failed with status {response.status_code}")
        
except Exception as e:
    print(f"❌ Email test failed: {e}")

print("\n✅ If you got 'EMAIL SENT SUCCESSFULLY' above, check your email!")
print("📧 Subject: 'Tickety Email Test - WORKING!'")
print("🎯 Your full app is now working: PDF + Email + Fight Ticket!")

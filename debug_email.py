import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
api_key = os.environ.get('RESEND_API_KEY')

print("🔧 Email Debug Test")
print(f"API Key: {api_key[:15]}..." if api_key else "❌ No API key found")

if not api_key:
    print("❌ Check your .env file - RESEND_API_KEY is missing")
    exit(1)

# Test email
email_data = {
    "from": "Tickety <onboarding@resend.dev>",
    "to": ["AAMM5845@GMAIL.COM"], 
    "subject": "🧪 Tickety Email Test",
    "html": """
    <div style="font-family: Arial, sans-serif; padding: 20px;">
        <h2 style="color: #4CAF50;">✅ Email Working!</h2>
        <p>This is a test email from your Tickety app.</p>
        <p>If you see this, your email system is working correctly!</p>
    </div>
    """
}

print("\n📧 Sending test email to AAMM5845@GMAIL.COM...")

try:
    response = requests.post(
        'https://api.resend.com/emails',
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        },
        json=email_data,
        timeout=10
    )
    
    print(f"📡 Status Code: {response.status_code}")
    print(f"📄 Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ EMAIL SENT SUCCESSFULLY!")
        print("📧 Check AAMM5845@GMAIL.COM inbox (and spam folder)")
    elif response.status_code == 422:
        print("❌ Email validation error - check email address or API key")
    elif response.status_code == 401:
        print("❌ API key is invalid or expired")
    else:
        print(f"❌ Email failed with status {response.status_code}")
        
except Exception as e:
    print(f"❌ Request failed: {e}")

print("\n🔍 Troubleshooting:")
print("1. Check spam folder")  
print("2. Verify API key is valid at resend.com")
print("3. Make sure email address is correct")

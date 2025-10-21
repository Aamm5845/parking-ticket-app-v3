import os
from dotenv import load_dotenv
load_dotenv()

import resend

# Test the new API key
resend.api_key = os.environ.get('RESEND_API_KEY')

print(f"Testing with API key: {resend.api_key[:10]}..." if resend.api_key else "No API key found")

try:
    email_params = {
        "from": "Tickety <onboarding@resend.dev>",
        "to": ["AAMM5845@GMAIL.COM"],
        "subject": "✅ Tickety Email Test - SUCCESS!",
        "html": """
        <div style="font-family: Arial, sans-serif; padding: 20px; background-color: #f0f8ff;">
            <h2 style="color: #2e8b57;">🎉 Email is Working!</h2>
            <p>Congratulations! Your Tickety app can now send emails successfully.</p>
            <p><strong>What this means:</strong></p>
            <ul>
                <li>✅ PDF receipts will be emailed automatically</li>
                <li>✅ You'll get your parking receipts in your inbox</li>
                <li>✅ Full app functionality is now working</li>
            </ul>
            <p style="margin-top: 30px; font-size: 12px; color: #666;">
                This test email was sent from your Tickety parking app.
            </p>
        </div>
        """
    }
    
    response = resend.Emails.send(email_params)
    print("✅ EMAIL SENT SUCCESSFULLY!")
    print(f"Response: {response}")
    print("\n🎯 Check your email inbox (including spam folder)")
    print("📧 Look for: 'Tickety Email Test - SUCCESS!'")
    
except Exception as e:
    print(f"❌ Email failed: {e}")
    print(f"Error type: {type(e)}")

import sys
print("Starting email test...", flush=True)

try:
    import os
    print("✅ OS imported", flush=True)
    
    from dotenv import load_dotenv
    print("✅ dotenv imported", flush=True)
    
    load_dotenv()
    print("✅ .env loaded", flush=True)
    
    api_key = os.environ.get('RESEND_API_KEY')
    if api_key:
        print(f"✅ API Key found: {api_key[:15]}...", flush=True)
    else:
        print("❌ No API key found in environment", flush=True)
        
        # Check .env file directly
        try:
            with open('.env', 'r') as f:
                content = f.read()
                if 'RESEND_API_KEY' in content:
                    print("✅ .env file contains RESEND_API_KEY", flush=True)
                else:
                    print("❌ .env file missing RESEND_API_KEY", flush=True)
        except FileNotFoundError:
            print("❌ No .env file found", flush=True)
            
    import requests
    print("✅ requests imported", flush=True)
    
    # Simple test
    if api_key:
        print(f"🧪 Testing with API key: {api_key}", flush=True)
        
        response = requests.post(
            'https://api.resend.com/emails',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                "from": "Tickety <onboarding@resend.dev>",
                "to": ["AAMM5845@GMAIL.COM"], 
                "subject": "Test from Tickety",
                "html": "<h1>Test Email</h1><p>If you see this, email works!</p>"
            }
        )
        
        print(f"📡 Response status: {response.status_code}", flush=True)
        print(f"📄 Response text: {response.text}", flush=True)
        
        if response.status_code == 200:
            print("✅ EMAIL SENT! Check AAMM5845@GMAIL.COM", flush=True)
        else:
            print("❌ Email failed", flush=True)
    
except Exception as e:
    print(f"❌ Error: {e}", flush=True)
    import traceback
    traceback.print_exc()

print("Test complete.", flush=True)

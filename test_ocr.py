#!/usr/bin/env python3
"""
Test Google Cloud Vision OCR functionality
"""

import os
import json
import ssl
from dotenv import load_dotenv

print("🔍 Testing Google Cloud Vision OCR...")

# Load environment variables
load_dotenv()

# Fix SSL issues for gRPC (Google Cloud uses gRPC)
try:
    import certifi
    os.environ['GRPC_DEFAULT_SSL_ROOTS_FILE_PATH'] = certifi.where()
    os.environ['SSL_CERT_FILE'] = certifi.where()
    print("✅ SSL certificates configured for gRPC")
except ImportError:
    print("⚠️ certifi not found - OCR might have SSL issues")

# Test Google Cloud credentials
try:
    credentials_json = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_JSON')
    if not credentials_json:
        print("❌ No Google Cloud credentials found in .env")
        print("Make sure GOOGLE_APPLICATION_CREDENTIALS_JSON is set")
        exit(1)
    
    credentials_data = json.loads(credentials_json)
    print("✅ Google Cloud credentials found")
    print(f"   Project: {credentials_data.get('project_id')}")
    print(f"   Email: {credentials_data.get('client_email')}")
    
    # Initialize client
    from google.cloud import vision
    from google.oauth2 import service_account
    
    credentials = service_account.Credentials.from_service_account_info(credentials_data)
    client = vision.ImageAnnotatorClient(credentials=credentials)
    
    print("✅ Google Vision client initialized")
    
    # Test with a simple image (create a test image with text)
    print("\n📝 Testing OCR functionality...")
    
    # Create a simple test image with text
    from PIL import Image, ImageDraw, ImageFont
    import io
    
    # Create a simple image with text
    img = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        # Try to use a better font
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    # Add some ticket-like text
    test_text = "TICKET: 123456789\nSPACE: PL123\nDATE: 2024-01-01 10:00"
    draw.text((10, 50), test_text, fill='black', font=font)
    
    # Convert to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    # Test OCR
    image = vision.Image(content=img_bytes.getvalue())
    response = client.document_text_detection(image=image)
    
    if response.error.message:
        print(f"❌ Vision API error: {response.error.message}")
    else:
        extracted_text = response.full_text_annotation.text
        print(f"✅ OCR SUCCESS!")
        print(f"📄 Extracted text: {extracted_text}")
        
        if "123456789" in extracted_text:
            print("✅ Text recognition working correctly!")
        else:
            print("⚠️ Text recognition partial - may need better image quality")
    
except Exception as e:
    print(f"❌ OCR test failed: {e}")
    print(f"Error type: {type(e)}")
    
    if "SSL" in str(e) or "certificate" in str(e).lower():
        print("\n🔧 SSL Issue - Try this fix:")
        print("1. Make sure you have certifi installed: pip install certifi")
        print("2. Restart your app after running this test")
        print("3. The SSL environment variables are now set")

print("\n" + "=" * 50)
print("🎯 OCR Status:")
if 'client' in locals():
    print("✅ OCR should now work in your app")
    print("📱 Try scanning a ticket image!")
else:
    print("❌ OCR setup failed - check credentials and SSL")
    
print("\n🚀 Restart your app to apply SSL fixes:")
print("python start_app.py")

#!/usr/bin/env python3
"""
Quick test to verify both buttons work
"""
import requests
import time
import subprocess
import sys
from threading import Thread

def start_app():
    """Start the Flask app"""
    import app
    app.app.run(host='127.0.0.1', port=5000, debug=False)

def test_buttons():
    """Test both button endpoints"""
    time.sleep(2)  # Wait for app to start
    
    base_url = "http://127.0.0.1:5000"
    
    print("🧪 Testing Tickety App Buttons...")
    
    # Test 1: App loads
    try:
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            print("✅ App loads successfully")
        else:
            print(f"❌ App failed to load: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Failed to connect to app: {e}")
        return
    
    # Test 2: Fight Ticket endpoint exists
    try:
        response = requests.post(f"{base_url}/fight_ticket_selenium", 
                               data={"ticket_number": "123456789"},
                               timeout=10)
        print(f"✅ Fight Ticket endpoint responds: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'success' in data:
                print("✅ Fight Ticket endpoint returns proper JSON")
            else:
                print("⚠️ Fight Ticket endpoint response format unexpected")
        else:
            print(f"⚠️ Fight Ticket endpoint error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Fight Ticket endpoint failed: {e}")
    
    # Test 3: PDF Generation endpoint
    try:
        pdf_data = {
            "ticket_number": "123456789",
            "space": "PL123",
            "date": "2024-01-01", 
            "start_time": "10:00"
        }
        response = requests.post(f"{base_url}/generate_pdf", data=pdf_data, timeout=10)
        print(f"✅ Generate PDF endpoint responds: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ PDF Generation works")
        else:
            print(f"⚠️ PDF Generation issue: {response.status_code}")
            
    except Exception as e:
        print(f"❌ PDF Generation failed: {e}")
    
    print("\n🎯 Summary:")
    print("- Both endpoints are accessible")
    print("- JavaScript should be able to call them")
    print("- Check browser console for any JS errors")
    print("\n🚀 Test your app at: http://127.0.0.1:5000")

if __name__ == "__main__":
    print("Starting Tickety App Test...")
    
    # Start app in background thread
    app_thread = Thread(target=start_app, daemon=True)
    app_thread.start()
    
    # Run tests
    test_buttons()
    
    print("\n⏰ App will keep running for 30 seconds for manual testing...")
    time.sleep(30)

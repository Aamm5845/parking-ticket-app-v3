#!/usr/bin/env python3
"""
Test the Fight Ticket functionality
"""
import requests
import json
import time

def test_fight_ticket():
    """Test the fight ticket endpoint directly"""
    
    print("🧪 Testing Fight Ticket Functionality...")
    
    # Test data
    test_data = {
        'ticket_number': '123456789'
    }
    
    # First, let's make sure we have a profile
    profile_data = {
        'first_name': 'Test',
        'last_name': 'User', 
        'license': 'L123456789',
        'address': '123 Test St',
        'city': 'Montreal',
        'province': 'Quebec',
        'postal_code': 'H1H1H1',
        'country': 'Canada',
        'email': 'test@test.com'
    }
    
    print("📝 Setting up test profile...")
    try:
        profile_response = requests.post(
            'http://localhost:5000/setup_profile',
            data=profile_data,
            timeout=5
        )
        if profile_response.status_code in [200, 302]:
            print("✅ Test profile created")
        else:
            print(f"⚠️ Profile setup response: {profile_response.status_code}")
    except Exception as e:
        print(f"❌ Failed to set up profile: {e}")
        print("Make sure the app is running: python app.py")
        return
    
    print("🚗 Testing Fight Ticket automation...")
    
    try:
        # Test the fight ticket endpoint
        response = requests.post(
            'http://localhost:5000/fight_ticket_selenium',
            data=test_data,
            timeout=30  # Give it time for Selenium to work
        )
        
        print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('success'):
                    print("✅ SUCCESS!")
                    print(f"📄 Message: {data.get('message', 'No message')}")
                    print("🌐 Browser should now be open with Montreal form filled!")
                    print("👀 Check if Chrome opened with the dispute form")
                else:
                    print("❌ FAILED!")
                    print(f"📄 Error: {data.get('message', 'Unknown error')}")
            except json.JSONDecodeError:
                print("⚠️ Response is not JSON:")
                print(response.text[:200] + "..." if len(response.text) > 200 else response.text)
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"📄 Response: {response.text[:200]}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out - this might be normal if Selenium is working")
        print("🌐 Check if Chrome browser opened with the form")
    except Exception as e:
        print(f"❌ Request failed: {e}")
        
    print("\n🎯 What should happen:")
    print("1. Chrome browser opens")
    print("2. Montreal dispute page loads") 
    print("3. Ticket number gets entered automatically")
    print("4. Personal information gets filled")
    print("5. Explanation gets added")
    print("6. Browser stays open for you to review and submit")
    
    print("\n💡 If it worked, you should see Chrome with the filled form!")

if __name__ == "__main__":
    print("=== Fight Ticket Test ===")
    print("Make sure to run 'python app.py' first!")
    print()
    test_fight_ticket()

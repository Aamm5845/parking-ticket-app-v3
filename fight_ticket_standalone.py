#!/usr/bin/env python3
"""
Standalone ticket fighting script - works perfectly without Flask complications
Just enter your ticket number and it will auto-fill the Montreal dispute form
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import random
import json
import os

# --- CONFIG ---
driver_path = r"C:\Users\ADMIN\Desktop\chromedriver.exe"
use_webdriver_manager = False  # Set to False - webdriver-manager has version issues
profile_file = "profile.json"

# Load profile from file if it exists
def load_profile():
    if os.path.exists(profile_file):
        try:
            with open(profile_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Could not load profile: {e}")
    return None

def save_profile(data):
    with open(profile_file, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"✅ Profile saved to {profile_file}")

def main():
    # Get ticket number
    ticket_number = input("Enter 9-digit ticket number: ").strip()
    if not ticket_number or len(ticket_number) != 9 or not ticket_number.isdigit():
        print("❌ Invalid ticket number. Must be 9 digits.")
        return
    
    # Try to load profile
    profile = load_profile()
    if not profile:
        print("\n⚙️ Setting up profile...")
        profile = {
            'first_name': input("First name: "),
            'last_name': input("Last name: "),
            'licence': input("Licence number: "),
            'address': input("Address: "),
            'city': input("City: "),
            'postal_code': input("Postal code: "),
            'email': input("Email: ")
        }
        save_profile(profile)
    else:
        print(f"✅ Using saved profile: {profile['first_name']} {profile['last_name']}")
    
    # --- START SELENIUM ---
    print("\n🌐 Starting Chrome browser...")
    try:
        # Try webdriver-manager first (auto-downloads matching ChromeDriver)
        if use_webdriver_manager:
            print("🔄 Forcing fresh ChromeDriver download for Chrome 141...")
            try:
                # Force clear cache and download latest
                from webdriver_manager.core.driver_cache import DriverCacheManager
                DriverCacheManager().remove_all()
                print("♾️ Cleared old ChromeDriver cache")
                
                # Download fresh ChromeDriver
                manager = ChromeDriverManager()
                service = Service(manager.install())
                print("✅ Downloaded fresh ChromeDriver matching your Chrome 141")
                
            except Exception as wdm_error:
                print(f"⚠️ WebDriver Manager failed: {wdm_error}")
                print(f"Falling back to manual ChromeDriver at: {driver_path}")
                if os.path.exists(driver_path):
                    service = Service(driver_path)
                else:
                    raise Exception(f"ChromeDriver not found. Please download ChromeDriver 141 from https://googlechromelabs.github.io/chrome-for-testing/")
        else:
            service = Service(driver_path)
        
        driver = webdriver.Chrome(service=service)
        driver.maximize_window()
        wait = WebDriverWait(driver, 20)
        print("✅ Chrome started successfully")
        
    except Exception as start_error:
        print(f"❌ Failed to start Chrome: {start_error}")
        print("\n⚠️ Troubleshooting:")
        print("1. Make sure Google Chrome is installed")
        print("2. The ChromeDriver version must match your Chrome version")
        print("3. Your Chrome is version 141, so you need ChromeDriver 141")
        print("4. Try updating ChromeDriver from: https://googlechromelabs.github.io/chrome-for-testing/")
        input("Press Enter to exit...")
        return
    
    try:
        # Open Montreal site
        print("📍 Opening Montreal dispute page...")
        driver.get("https://services.montreal.ca/plaidoyer/rechercher/en")
        
        # Step 1: Enter ticket number
        print(f"🔍 Entering ticket number: {ticket_number}")
        wait.until(EC.presence_of_element_located((By.ID, "searchTxtStatementNo"))).send_keys(ticket_number)
        wait.until(EC.element_to_be_clickable((By.ID, "searchBtnSubmit"))).click()
        
        # Step 2: Choose "person whose name appears"
        print("👤 Selecting person type...")
        wait.until(EC.presence_of_element_located((By.ID, "who")))
        dropdown = driver.find_element(By.ID, "who")
        dropdown.click()
        dropdown.find_element(By.CSS_SELECTOR, "option[value='1']").click()
        
        # Step 3: Fill personal info
        print("📝 Filling personal information...")
        wait.until(EC.presence_of_element_located((By.ID, "firstName"))).send_keys(profile['first_name'])
        driver.find_element(By.ID, "lastName").send_keys(profile['last_name'])
        driver.find_element(By.ID, "licenceNumber").send_keys(profile['licence'])
        driver.find_element(By.ID, "address").send_keys(profile['address'])
        driver.find_element(By.ID, "city").send_keys(profile['city'])
        driver.find_element(By.ID, "postalCode").send_keys(profile['postal_code'])
        driver.find_element(By.ID, "email").send_keys(profile['email'])
        driver.find_element(By.ID, "confEmail").send_keys(profile['email'])
        
        # Step 4: Add explanation
        print("💬 Adding explanation...")
        messages = [
            "I had paid for parking through the app, but the officer issued the ticket just a few minutes before the transaction was processed.",
            "I am pleading not guilty because I paid using the app at the time of parking. The ticket was issued just before or right after payment was confirmed.",
            "I received a parking ticket even though I had paid using the parking app. The ticket was likely issued within a very short window before the payment was processed."
        ]
        driver.find_element(By.ID, "explanation").send_keys(random.choice(messages))
        
        print("\n✅ All fields filled successfully!")
        print("📋 Please review the information and submit manually.")
        print("🔓 Press Enter to close the browser when finished...")
        input()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        driver.quit()
        print("👋 Browser closed.")

if __name__ == "__main__":
    main()

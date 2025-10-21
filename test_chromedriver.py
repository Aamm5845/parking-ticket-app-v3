#!/usr/bin/env python3
"""
Test script to verify ChromeDriver setup
"""
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

def test_chromedriver():
    print("🧪 Testing ChromeDriver setup...")
    
    driver_path = r"C:\Users\ADMIN\Desktop\chromedriver.exe"
    
    # Check if chromedriver exists
    if os.path.exists(driver_path):
        print(f"✅ ChromeDriver found at: {driver_path}")
    else:
        print(f"❌ ChromeDriver NOT found at: {driver_path}")
        print("Please download ChromeDriver from: https://chromedriver.chromium.org/")
        return False
    
    # Test launching Chrome
    try:
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print("✅ Chrome launched successfully!")
        
        # Test basic navigation
        driver.get("https://www.google.com")
        print("✅ Successfully navigated to Google")
        
        # Test Montreal website
        driver.get("https://services.montreal.ca/plaidoyer/rechercher/en")
        print("✅ Successfully opened Montreal dispute page")
        
        driver.quit()
        print("✅ ChromeDriver test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ ChromeDriver test failed: {e}")
        return False

if __name__ == "__main__":
    print("=== ChromeDriver Test ===")
    success = test_chromedriver()
    
    if success:
        print("\n🎉 Your setup is ready!")
        print("The Fight Ticket button should now work properly.")
    else:
        print("\n🔧 Setup issues found. Please fix ChromeDriver installation.")
        print("1. Download ChromeDriver from: https://chromedriver.chromium.org/")
        print("2. Place it at: C:\\Users\\ADMIN\\Desktop\\chromedriver.exe")
        print("3. Make sure Chrome browser version matches ChromeDriver version")

# 🎫 Standalone Ticket Fighting Script

Simple, direct way to fight your parking ticket with one click!

## Quick Start

### Double-Click to Run
1. **Double-click** `fight_ticket.bat` in the parking-ticket-app-v2 folder
2. Enter your **9-digit ticket number**
3. Chrome will open and auto-fill the Montreal dispute form
4. Review and submit!

## How It Works

1. **First run**: You'll be asked to enter your profile info (name, license, address, etc.)
   - This gets saved so you only need to enter it once

2. **Subsequent runs**: Just enter the ticket number
   - Your profile is remembered and used automatically

3. **Chrome opens**: Automatically fills all fields on the Montreal dispute page
4. **Review**: Check everything is correct, then submit manually

## Features

✅ **No Flask complications** - Pure Selenium script  
✅ **Profile saved** - Remember your info for next time  
✅ **Auto-fills everything** - All form fields filled automatically  
✅ **Manual review** - You control the final submission  
✅ **Uses your working code** - Based on your proven Selenium script  

## What Gets Saved

After the first run, your profile is saved in `profile.json`:
- First name
- Last name
- License number
- Address
- City
- Postal code
- Email

You can edit `profile.json` directly if needed, or just re-run the script to update it.

## Troubleshooting

**"ChromeDriver not found"**
- Make sure `chromedriver.exe` is at `C:\Users\ADMIN\Desktop\chromedriver.exe`
- Or update the path in `fight_ticket_standalone.py` line 17

**Chrome doesn't open**
- Make sure Google Chrome is installed
- Check that chromedriver matches your Chrome version

**Fields aren't filling**
- The Montreal website might have changed
- Check the browser console for JavaScript errors
- You can still fill manually using the web app

## Comparison

| Method | Speed | Reliability | Setup |
|--------|-------|-------------|-------|
| **Standalone Script** | ⚡ Very Fast | ✅ Works | Simple |
| **Web App + Bookmarklet** | 🟢 Fast | ✅ Works | One-time |
| **Web App + Selenium** | 🟢 Fast | ❌ Issues | Complex |

**Recommendation**: Use the standalone script for the most reliable, direct automation! 🚀
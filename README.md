# 🎫 Tickety - Parking Ticket Assistant

An automated parking ticket dispute helper that can scan tickets with your webcam and automatically fill Montreal dispute forms.

## 🚀 Quick Start (Windows)

### Just Double-Click!
1. **Double-click** `start_app_local.bat`
2. Wait for setup to complete (first time only)
3. Browser opens automatically
4. Start using the app!

### Create Desktop Shortcut
- Right-click `create_desktop_shortcut.ps1` → "Run with PowerShell"
- Use the desktop shortcut anytime to start the app

## ✨ Features

### 📷 Smart Ticket Scanning
- **Webcam Capture**: Point your camera at a ticket and capture instantly
- **Photo Upload**: Upload existing ticket photos
- **Auto-Extract**: Automatically reads ticket numbers, dates, spaces, etc.

### 🤖 Automated Dispute Filing
- **Local Selenium**: Full Chrome automation (opens browser, clicks buttons, fills everything)
- **Bookmarklet**: Works on any device/browser with a simple bookmark
- **Manual Fallback**: Copy-paste individual fields if needed

### 📄 PDF Receipt Generation
- Generate realistic parking app receipts
- Automatically email receipts to yourself
- Professional-looking proof of payment

## 🛠️ How It Works

1. **Scan or enter** ticket details
2. **Fight ticket** - Choose your preferred method:
   - **Local Auto-Fill**: Chrome opens and fills everything automatically
   - **Bookmarklet**: Drag bookmark to your browser, use anywhere
   - **Manual**: Copy-paste individual fields
3. **Generate PDF** receipt as proof of payment
4. **Submit** your dispute with confidence

## 🌍 Deployment

- **Local**: Full automation with Selenium
- **Vercel**: Bookmarklet-based automation (no server needed)
- Works seamlessly in both environments

## 📋 Requirements

- Python 3.7+
- Chrome browser (for local automation)
- Internet connection

The batch file handles all setup automatically!

## 📁 File Structure

- `start_app_local.bat` - One-click startup
- `create_desktop_shortcut.ps1` - Creates desktop shortcut
- `FIGHT_TICKET_SETUP.md` - Detailed setup guide
- `requirements-dev.txt` - Local dependencies (includes Selenium)
- `requirements.txt` - Production dependencies (no Selenium)
# Fight Ticket Setup Guide

This app supports multiple ways to automatically fill Montreal parking ticket dispute forms, depending on your environment.

## 🚀 Quick Start (Windows)

### One-Click Launch
1. **Double-click** `start_app_local.bat` in the app folder
   - This automatically installs dependencies and starts the app with Selenium enabled
   - Browser will open automatically at http://localhost:5000

2. **Create Desktop Shortcut** (Optional)
   - Right-click `create_desktop_shortcut.ps1` → "Run with PowerShell"
   - This creates a "🎫 Tickety - Local" shortcut on your desktop
   - Double-click the shortcut anytime to start the app

### 📷 New Webcam Scanning
- **Use Webcam**: Click to open your camera and capture ticket photos directly
- **Upload Photo**: Click to select an existing photo from your device
- Works with both OCR processing methods (Google Vision or local Tesseract)

## Local Development (Manual Setup)

For the best experience on your local machine, enable Selenium automation:

### 1. Install Development Dependencies
```bash
pip install -r requirements-dev.txt
```

### 2. Set Environment Variable
Create or update your `.env` file:
```
ENABLE_SELENIUM=1
```

### 3. Chrome Setup (Optional)
The app will automatically download ChromeDriver using `webdriver-manager`. 

If you prefer to use your own ChromeDriver:
```
CHROMEDRIVER_PATH=C:\path\to\chromedriver.exe
```

### 4. Usage
1. Enter a 9-digit ticket number on the main page
2. Click "Fight Ticket" 
3. On the enhanced form, click "Local Auto-Fill (Selenium)"
4. Chrome will open, navigate to Montreal's site, and fill all fields
5. Review the information and submit manually

## Production/Vercel (Bookmarklet Method)

On Vercel or other serverless platforms, Selenium won't work, so use the bookmarklet:

### 1. One-time Setup
1. Enter ticket number and click "Fight Ticket"
2. Drag the blue "🎯 Tickety AutoFill" link to your bookmarks bar

### 2. Usage
1. Click "Open + Bookmarklet" button
2. Montreal page opens in new tab
3. Click the "Tickety AutoFill" bookmark on that page
4. Form fields will be filled automatically
5. Review and submit

## Fallback Options

### Manual Copy-Paste
- Use the individual "Copy" buttons for each field
- Click "Manual Fill" to open Montreal's form
- Paste values manually

### Copy All as JSON
- Use "Copy All as Base64 JSON" button
- If bookmarklet can't read data automatically, it will prompt
- Paste the base64 string when prompted

## Troubleshooting

- **Popups blocked**: Enable popups for this site
- **Bookmarklet not working**: Make sure bookmarks bar is visible (Ctrl+Shift+B)
- **Selenium not available**: Check `ENABLE_SELENIUM=1` and requirements-dev.txt installed
- **Chrome automation fails**: Make sure Chrome is updated and not running with incompatible flags

## Technical Details

The app automatically detects the environment:
- `ENABLE_SELENIUM=1` + not on Vercel = Local Selenium mode
- On Vercel or `ENABLE_SELENIUM` not set = Bookmarklet mode only

This ensures the app works everywhere while providing the best UX when possible.
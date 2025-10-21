# 🔧 Debug Both Buttons

## Quick Fix Steps

1. **Start the app:**
   ```bash
   python app.py
   ```

2. **Open in browser:** http://localhost:5000

3. **Open Developer Tools:**
   - Press `F12` in your browser
   - Go to the "Console" tab
   - You should see: `✅ Page loaded`

4. **Set up profile first:**
   - Click "Set Up My Profile"
   - Fill in your information
   - Click "Save Profile"

5. **Test Generate PDF Button:**
   - Fill in ticket details:
     - Ticket Number: `123456789`
     - Space Number: `PL123`  
     - Date: Today's date
     - Start Time: Any time
   - Click "Generate PDF"
   - **Expected:** PDF downloads & email sent

6. **Test Fight Ticket Button:**
   - Enter Ticket Number: `123456789`
   - Click "Fight Ticket"
   - **Expected:** Chrome opens with Montreal form filled

## Debug Console Messages

You should see these in browser console:

```
✅ Page loaded
✅ Generate button found
✅ Fight button found
Fight ticket clicked (when you click)
Response status: 200 (or error)
```

## Common Issues & Solutions

### Issue 1: "Fight button or ticket input not found"
**Solution:** Make sure you've set up your profile first

### Issue 2: PDF button doesn't work
**Solution:** Check if all form fields are filled

### Issue 3: Fight ticket says "Profile not found"
**Solution:** Set up your profile in the app

### Issue 4: Selenium fails
**Solution:** Run ChromeDriver test:
```bash
python test_chromedriver.py
```

### Issue 5: No console messages
**Solution:** Hard refresh the page (Ctrl+F5)

## Manual Test

If buttons still don't work, test manually:

1. **Test PDF endpoint directly:**
   Open: http://localhost:5000/generate_pdf
   
2. **Test Fight ticket endpoint:**
   ```bash
   curl -X POST http://localhost:5000/fight_ticket_selenium -d "ticket_number=123456789"
   ```

## Quick Test Script

Run this to test everything:
```bash
python test_buttons.py
```

This will verify both endpoints work correctly.

# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Application Overview

Tickety is a Flask-based web application that helps users fight Montreal parking tickets by:
1. Scanning or manually entering parking ticket details
2. Generating fake parking receipts as PDF documents
3. Automatically emailing receipts to users
4. Providing automated form-filling for Montreal's ticket dispute system

This is a Progressive Web App (PWA) with offline capabilities, designed as a mobile-first experience.

## Core Architecture

### Backend (Flask)
- **Main Application**: `app.py` - Single file Flask application with all routes and business logic
- **Profile Management**: JSON-based user profile storage (`profile.json`)
- **PDF Generation**: Uses ReportLab + PyPDF2 to overlay data onto a base template PDF
- **OCR Integration**: Google Cloud Vision API for automatic ticket scanning
- **Email Service**: Resend API for sending generated PDFs

### Frontend (Templates + JavaScript)
- **Template Engine**: Jinja2 templates in `templates/` directory
- **Styling**: Single CSS file at `static/style.css` with CSS custom properties
- **PWA Support**: Service worker (`sw.js`) and manifest (`static/manifest.json`)
- **Mobile-First**: Responsive design optimized for mobile devices

### Key Data Flow
1. **Profile Setup** → User enters personal information (stored in `profile.json`)
2. **Ticket Processing** → Camera OCR or manual entry → Form validation
3. **PDF Generation** → Overlay ticket data onto `base_template.pdf` using coordinates from CSV
4. **Email Delivery** → Send PDF + autofill link via Resend API
5. **Ticket Fighting** → Automated form filling on Montreal's dispute website

## Development Commands

### Local Development
```bash
# Set up virtual environment (Windows)
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
copy .env.example .env
# Edit .env with your actual API keys

# Run development server
python app.py
# Access at: http://localhost:5000
```

### Environment Setup
```bash
# Required environment variables (see .env.example)
SECRET_KEY=your_flask_secret_key
RESEND_API_KEY=your_resend_api_key
GOOGLE_APPLICATION_CREDENTIALS_JSON=your_gcp_credentials_json
```

### Deployment

**Vercel Deployment:**
```bash
# Deploy using Vercel CLI
vercel deploy
```

**Render/Heroku Deployment:**
```bash
# Uses Procfile for gunicorn configuration
# Build script: ./build.sh (simplified - no external dependencies)
gunicorn app:app
```

## Environment Variables

Required environment variables:
- `SECRET_KEY` - Flask secret key for sessions
- `RESEND_API_KEY` - Resend email service API key
- `GOOGLE_APPLICATION_CREDENTIALS_JSON` - Google Cloud Vision API credentials (JSON string)

Create a `.env` file based on `.env.example` for local development.

## Key Files and Directories

### Core Application
- `app.py` - Main Flask application with all routes and business logic
- `requirements.txt` - Python dependencies
- `Procfile` - Production server configuration
- `build.sh` - Build script for Tesseract OCR installation
- `vercel.json` - Vercel deployment configuration

### Static Assets
- `static/style.css` - Complete application styling
- `static/base_template.pdf` - Base PDF template for receipt generation
- `static/Mobicite_Placeholder_Locations.csv` - Coordinate mapping for PDF overlay
- `static/manifest.json` - PWA manifest
- `sw.js` - Service worker for offline functionality

### Templates
- `templates/index.html` - Main application interface
- `templates/profile_setup.html` - User profile configuration
- `templates/fight_ticket.html` - Advanced client-side form filling interface
- `templates/autofill_script.html` - Legacy autofill (deprecated)

### Configuration
- `.gitignore` - Excludes JSON files (contains profile data)
- `profile.json` - User profile storage (git-ignored)

## External Services Integration

### Google Cloud Vision API
- Used for OCR ticket scanning functionality
- Extracts ticket number, space number, date, and time from images
- Regex patterns in `scan_ticket()` route parse the OCR results

### Resend Email API
- Sends generated PDF receipts to users
- Includes autofill link for dispute form
- Email templates embedded in `generate_pdf()` route

### Montreal Ticket Dispute System
- `/fight_ticket` route provides advanced client-side form automation
- `templates/fight_ticket.html` creates popup window with automated field filling
- Copy-to-clipboard functionality for manual fallback
- Cross-origin JavaScript attempts to fill Montreal's dispute form
- Form field mappings hardcoded for Montreal's specific form structure

## Development Notes

### PDF Generation Process
1. Load base template from `static/base_template.pdf`
2. Create overlay using ReportLab Canvas with data from form
3. Use CSV coordinates (`Mobicite_Placeholder_Locations.csv`) for positioning
4. Merge overlay with base template using PyPDF2
5. Generate random transaction numbers and timestamps

### Profile Management
- Profiles stored as JSON in local filesystem or `/tmp` on Vercel
- No database - uses file-based storage
- Profile data auto-populates dispute forms

### Mobile PWA Features
- Service worker caches static assets
- Manifest enables "Add to Home Screen"
- Camera integration for ticket scanning
- Responsive design with mobile-first approach

### Form Filling Architecture
- **Client-Side Automation**: JavaScript attempts cross-origin form filling
- **Fallback System**: Copy-to-clipboard functionality for manual entry
- **Multi-Step Process**: Automated ticket search → personal info → explanation
- **User Feedback**: Real-time status updates during automation process
- **Browser Compatibility**: Works with popup blockers and CORS restrictions

## Security Considerations

- API keys are properly configured via environment variables (`.env` file)
- Profile data contains sensitive information (stored in git-ignored files)
- Application generates fake receipts - ensure legal compliance in your jurisdiction
- Cross-origin form filling may be blocked by browsers due to security policies
- Email sending requires valid RESEND_API_KEY and domain verification

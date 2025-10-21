# Environment Variables Setup for Heroku
# Run this after creating your Heroku app

Write-Host "🔐 Setting up environment variables for Heroku..." -ForegroundColor Green

# Get the Heroku app name
$appName = Read-Host "Enter your Heroku app name"

# SECRET_KEY
Write-Host "⚙️ Setting SECRET_KEY..." -ForegroundColor Yellow
$secretKey = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | % {[char]$_})
heroku config:set SECRET_KEY=$secretKey --app $appName

# RESEND_API_KEY (for email functionality)
Write-Host "📧 Setting RESEND_API_KEY..." -ForegroundColor Yellow
$resendKey = Read-Host "Enter your Resend API key (from resend.com) or press Enter to skip"
if ($resendKey) {
    heroku config:set RESEND_API_KEY=$resendKey --app $appName
    Write-Host "✅ Resend API key set" -ForegroundColor Green
} else {
    Write-Host "⏭️ Skipping Resend API key (email features will be disabled)" -ForegroundColor Yellow
}

# GOOGLE_APPLICATION_CREDENTIALS_JSON (for OCR functionality)
Write-Host "👁️ Setting Google Cloud Vision API credentials..." -ForegroundColor Yellow
Write-Host "This is a JSON string from your Google Cloud service account key file" -ForegroundColor Cyan
$googleCreds = Read-Host "Enter your Google Cloud credentials JSON string or press Enter to skip"
if ($googleCreds) {
    heroku config:set GOOGLE_APPLICATION_CREDENTIALS_JSON=$googleCreds --app $appName
    Write-Host "✅ Google Cloud credentials set" -ForegroundColor Green
} else {
    Write-Host "⏭️ Skipping Google Cloud credentials (OCR features will be disabled)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✅ Environment variables setup complete!" -ForegroundColor Green
Write-Host "📋 Current config vars:" -ForegroundColor Cyan
heroku config --app $appName

Write-Host ""
Write-Host "📝 Note: You can update these later with:" -ForegroundColor Yellow
Write-Host "heroku config:set VARIABLE_NAME=value --app $appName" -ForegroundColor White

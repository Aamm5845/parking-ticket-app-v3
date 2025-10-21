# Environment Variables Setup for Heroku
Write-Host "Setting up environment variables for Heroku..." -ForegroundColor Green

# Get the Heroku app name
$appName = Read-Host "Enter your Heroku app name"

# Generate and set SECRET_KEY
Write-Host "Setting SECRET_KEY..." -ForegroundColor Yellow
$chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
$secretKey = ""
for ($i = 0; $i -lt 32; $i++) {
    $secretKey += $chars[(Get-Random -Maximum $chars.Length)]
}
heroku config:set SECRET_KEY=$secretKey --app $appName

# Set RESEND_API_KEY (optional)
Write-Host "Setting RESEND_API_KEY for email functionality..." -ForegroundColor Yellow
Write-Host "If you don't have one, get it from: https://resend.com" -ForegroundColor Cyan
$resendKey = Read-Host "Enter your Resend API key (or press Enter to skip)"
if ($resendKey) {
    heroku config:set RESEND_API_KEY=$resendKey --app $appName
    Write-Host "Resend API key set" -ForegroundColor Green
} else {
    Write-Host "Skipping Resend API key (email features will be disabled)" -ForegroundColor Yellow
}

# Set Google Cloud credentials (optional)
Write-Host "Setting Google Cloud Vision API credentials for OCR..." -ForegroundColor Yellow
Write-Host "This should be the JSON content from your Google Cloud service account key" -ForegroundColor Cyan
$googleCreds = Read-Host "Enter your Google Cloud credentials JSON (or press Enter to skip)"
if ($googleCreds) {
    heroku config:set GOOGLE_APPLICATION_CREDENTIALS_JSON=$googleCreds --app $appName
    Write-Host "Google Cloud credentials set" -ForegroundColor Green
} else {
    Write-Host "Skipping Google Cloud credentials (OCR features will be disabled)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Environment variables setup complete!" -ForegroundColor Green
Write-Host "Current config vars:" -ForegroundColor Cyan
heroku config --app $appName

Write-Host ""
Write-Host "You can update these later with:" -ForegroundColor Yellow
Write-Host "heroku config:set VARIABLE_NAME=value --app $appName" -ForegroundColor White

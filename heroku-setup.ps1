# Heroku Deployment Script for Parking Ticket App
# Run this after installing Heroku CLI

Write-Host "🚀 Setting up Heroku deployment for parking-ticket-app..." -ForegroundColor Green

# Check if Heroku CLI is installed
try {
    heroku --version
    Write-Host "✅ Heroku CLI found" -ForegroundColor Green
} catch {
    Write-Host "❌ Please install Heroku CLI first from: https://devcenter.heroku.com/articles/heroku-cli" -ForegroundColor Red
    exit 1
}

# Login to Heroku (if not already logged in)
Write-Host "🔐 Logging into Heroku..." -ForegroundColor Yellow
heroku login

# Create Heroku app (replace parking-ticket-app with your preferred name)
$appName = Read-Host "Enter your app name (e.g., my-parking-app)"
Write-Host "🏗️ Creating Heroku app: $appName" -ForegroundColor Yellow
heroku create $appName

# Add required buildpacks for Chrome and Python
Write-Host "📦 Adding Python buildpack..." -ForegroundColor Yellow
heroku buildpacks:add heroku/python --app $appName

Write-Host "📦 Adding Chrome buildpack for Selenium..." -ForegroundColor Yellow
heroku buildpacks:add https://github.com/heroku/heroku-buildpack-chrome-for-testing.git --app $appName

# Initialize git if not already done
if (!(Test-Path ".git")) {
    Write-Host "🔧 Initializing git repository..." -ForegroundColor Yellow
    git init
    git add .
    git commit -m "Initial commit for Heroku deployment"
}

# Add Heroku remote
Write-Host "🔗 Adding Heroku remote..." -ForegroundColor Yellow
heroku git:remote -a $appName

Write-Host "✅ Heroku setup complete!" -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Set your environment variables with: .\set-env-vars.ps1" -ForegroundColor White
Write-Host "2. Deploy with: git push heroku main" -ForegroundColor White

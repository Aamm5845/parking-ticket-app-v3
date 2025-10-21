# Heroku Deployment Script for Parking Ticket App
Write-Host "Setting up Heroku deployment..." -ForegroundColor Green

# Check if Heroku CLI is installed
try {
    $version = heroku --version
    Write-Host "Heroku CLI found: $version" -ForegroundColor Green
} catch {
    Write-Host "Please install Heroku CLI first from: https://devcenter.heroku.com/articles/heroku-cli" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Login to Heroku
Write-Host "Logging into Heroku..." -ForegroundColor Yellow
heroku login

# Get app name from user
$appName = Read-Host "Enter your app name (letters and dashes only, e.g. my-parking-app)"

# Create Heroku app
Write-Host "Creating Heroku app: $appName" -ForegroundColor Yellow
heroku create $appName

# Add Python buildpack
Write-Host "Adding Python buildpack..." -ForegroundColor Yellow
heroku buildpacks:add heroku/python --app $appName

# Add Chrome buildpack for Selenium
Write-Host "Adding Chrome buildpack for Selenium..." -ForegroundColor Yellow
heroku buildpacks:add https://github.com/heroku/heroku-buildpack-chrome-for-testing.git --app $appName

# Initialize git if needed
if (!(Test-Path ".git")) {
    Write-Host "Initializing git repository..." -ForegroundColor Yellow
    git init
    git add .
    git commit -m "Initial commit for Heroku deployment"
}

# Add Heroku remote
Write-Host "Adding Heroku remote..." -ForegroundColor Yellow
heroku git:remote -a $appName

Write-Host "Heroku setup complete!" -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Set environment variables: .\set-env-vars-fixed.ps1" -ForegroundColor White
Write-Host "2. Deploy: git push heroku main" -ForegroundColor White
Write-Host ""
Write-Host "Your app will be available at: https://$appName.herokuapp.com" -ForegroundColor Yellow

# PowerShell script to create desktop shortcut for Tickety app
Write-Host "Creating desktop shortcut for Tickety..." -ForegroundColor Green

$desktopPath = [System.Environment]::GetFolderPath('Desktop')
$shortcutPath = Join-Path $desktopPath "🎫 Tickety - Local.lnk"
$targetPath = Join-Path $PSScriptRoot "start_app_local.bat"
$iconPath = Join-Path $PSScriptRoot "static\logo.png"

# Create WScript Shell object
$WScriptShell = New-Object -ComObject WScript.Shell

# Create the shortcut
$shortcut = $WScriptShell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $targetPath
$shortcut.WorkingDirectory = $PSScriptRoot
$shortcut.Description = "Start Tickety parking ticket app with Selenium automation"

# Set icon if available (Windows will use default batch file icon otherwise)
if (Test-Path $iconPath) {
    $shortcut.IconLocation = $iconPath
}

# Save the shortcut
$shortcut.Save()

Write-Host "✅ Desktop shortcut created successfully!" -ForegroundColor Green
Write-Host "📍 Shortcut location: $shortcutPath" -ForegroundColor Yellow
Write-Host ""
Write-Host "You can now double-click the '🎫 Tickety - Local' shortcut on your desktop to start the app!" -ForegroundColor Cyan

# Release COM object
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($WScriptShell) | Out-Null

Read-Host "Press Enter to continue..."
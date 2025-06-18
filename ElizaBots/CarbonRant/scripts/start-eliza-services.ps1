# start-eliza-services.ps1
# Script to start ElizaServices for Twitter popularity checking

Write-Host "Starting ElizaServices for Twitter popularity checking..."
$elizaServicesPath = "c:\Users\tanny\OneDrive\Desktop\carbontruth\ElizaServices\elizaservices"
Set-Location -Path $elizaServicesPath
python manage.py runserver 8000

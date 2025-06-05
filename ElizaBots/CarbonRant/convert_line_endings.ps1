$content = Get-Content -Path 'C:\Users\tanny\OneDrive\Desktop\carbontruth\ElizaBots\CarbonRant\client\version.sh' -Raw
$content = $content -replace "`r`n", "`n"
Set-Content -Path 'C:\Users\tanny\OneDrive\Desktop\carbontruth\ElizaBots\CarbonRant\client\version.sh' -Value $content -NoNewline
Write-Host "Converted line endings in version.sh"

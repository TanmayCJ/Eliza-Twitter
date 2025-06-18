# This script sets environment variables for testing the tweet popularity feature
# with the ElizaServices API

# Set environment variables for the test
$env:TWITTER_POPULARITY_API_URL = "http://127.0.0.1:8000/api/popularity/"
$env:TWITTER_POPULARITY_CHECK_ENABLED = "true"
$env:TWITTER_POPULARITY_MIN_SCORE = "30"
$env:TWITTER_POPULARITY_VERBOSE_OUTPUT = "true"

Write-Host "Environment variables set:"
Write-Host "- TWITTER_POPULARITY_API_URL: $env:TWITTER_POPULARITY_API_URL"
Write-Host "- TWITTER_POPULARITY_CHECK_ENABLED: $env:TWITTER_POPULARITY_CHECK_ENABLED"
Write-Host "- TWITTER_POPULARITY_MIN_SCORE: $env:TWITTER_POPULARITY_MIN_SCORE"
Write-Host "- TWITTER_POPULARITY_VERBOSE_OUTPUT: $env:TWITTER_POPULARITY_VERBOSE_OUTPUT"

# Run the test script
Write-Host "`nRunning tweet popularity test..."
npx ts-node-esm ../ElizaBots/CarbonRant/scripts/test-popularity.ts

# Reset environment variables after test
$env:TWITTER_POPULARITY_API_URL = $null
$env:TWITTER_POPULARITY_CHECK_ENABLED = $null
$env:TWITTER_POPULARITY_MIN_SCORE = $null
$env:TWITTER_POPULARITY_VERBOSE_OUTPUT = $null

Write-Host "`nTest complete. Environment variables cleared."

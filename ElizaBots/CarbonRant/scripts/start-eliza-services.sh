#!/bin/bash
# start-eliza-services.sh
# Script to start ElizaServices for Twitter popularity checking

echo "Starting ElizaServices for Twitter popularity checking..."
cd "c:/Users/tanny/OneDrive/Desktop/carbontruth/ElizaServices/elizaservices"
python manage.py runserver 8000

#!/usr/bin/env bash

# Build script for deployment platforms
# Simplified since we removed Tesseract/Selenium dependencies

# Exit immediately if a command exits with a non-zero status.
set -e

# Install Python dependencies from requirements.txt.
pip install -r requirements.txt

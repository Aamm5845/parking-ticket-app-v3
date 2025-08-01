#!/usr/bin/env bash

# This script is a workaround for Render's build process.
# It ensures all dependencies are installed correctly.

# Exit immediately if a command exits with a non-zero status.
set -e

# Install Tesseract OCR and its development headers using apt-get.
# This command is a more robust way to install Tesseract on Render.
apt-get update -y && apt-get install -y tesseract-ocr libtesseract-dev libleptonica-dev

# Install Python dependencies from requirements.txt.
# This uses the virtual environment set up by Render.
pip install -r requirements.txt

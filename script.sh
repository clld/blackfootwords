#!/bin/bash

# Ensure the script stops if any command fails
set -e

# Detect the OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Detected macOS."
    INSTALL_CMD="brew install"
else
    echo "Detected Linux."
    INSTALL_CMD="sudo apt install -y"
fi

# Install pip
echo "Installing pip if not already installed..."
$INSTALL_CMD python3-pip

# Install virtualenv or python3-venv
echo "Installing virtual environment tools..."
if ! pip install virtualenv; then
    echo "Falling back to python3-venv..."
    $INSTALL_CMD python3-venv
fi

# Set up virtual environment
echo "Setting up virtual environment..."
if ! python3 -m virtualenv .venv; then
    echo "Falling back to python3-venv..."
    python3 -m venv .venv
fi

# Activate the virtual environment
echo "Activating the virtual environment..."
source .venv/bin/activate

# Install the current project in editable mode
echo "Installing project dependencies..."
pip install -e .

# Install additional dependencies
echo "Installing additional dependencies..."
pip install waitress pycldf -r requirements.txt

# Define the replacement shebang
var="#!/usr/bin/env python3"

# Define the target directory (relative path)
TARGET_DIR="./.venv/bin"

# Check if the target directory exists
if [ -d "$TARGET_DIR" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        find "$TARGET_DIR" -type f -exec sed -i '' "1s|.*|$var|" {} +
    else
        find "$TARGET_DIR" -type f -exec sed -i "1s|.*|$var|" {} +
    fi
    echo "All files in $TARGET_DIR updated with the new shebang line."
else
    echo "Directory $TARGET_DIR does not exist. Please check the path."
fi

# Initialize the database
echo "Initializing the database with CLDF metadata..."
clld initdb development.ini --cldf ~/blackfootwords-dataset/cldf/Wordlist-metadata.json

# Start the server
echo "Starting the server with pserve..."
pserve development.ini

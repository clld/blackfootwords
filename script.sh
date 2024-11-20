#!/bin/bash

# Ensure the script stops if any command fails
set -e

# Install pip (if not already installed)
echo "Installing pip if not already installed..."
sudo apt install -y python3-pip

# Install virtualenv or python3-venv
echo "Installing virtual environment tools..."
if ! pip install virtualenv; then
    echo "Falling back to python3-venv..."
    sudo apt install -y python3-venv
fi

# Set up virtual environment
echo "Setting up virtual environment..."
if ! python3 -m virtualenv .venv; then
    echo "Falling back to python3-venv..."
    python3 -m venv .venv

# Activate the virtual environment
echo "Activating the virtual evnrionment..."
source .venv/bin/activate

# Install the current project in editable mode
echo "Installing project dependencies..."
pip install -e .

# Install additional dependencies
echo "Installing additional dependencies..."
pip install waitress pycldf

# Install additional packages
pip install -r requirements.txt

# Initialize the database
echo "Initializing the database with CLDF metadata..."
clld initdb development.ini --cldf ~/blackfootwords/cldf/Wordlist-metadata.json

# Start the server
echo "Starting the server with pserve..."
pserve development.ini

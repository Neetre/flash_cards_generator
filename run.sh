#!/bin/bash

# Going to project dir
cd /site/flash_cards_generator

# Set variables
VENV_DIR=".venv"
NPM_DIR="bin"
PYTHON="python3"

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Check if Python is installed
if ! command_exists "$PYTHON"; then
  echo "Error: $PYTHON is not installed. Please install it and try again."
  exit 1
fi

# Set up the Python virtual environment if not present
if [ ! -d "$VENV_DIR" ]; then
  echo "Virtual environment not found. Creating one in $VENV_DIR..."
  "$PYTHON" -m venv "$VENV_DIR"
  if [ $? -ne 0 ]; then
    echo "Failed to create virtual environment."
    exit 1
  fi
fi

# Activate the virtual environment
source "$VENV_DIR/bin/activate"
if [ $? -ne 0 ]; then
  echo "Failed to activate virtual environment."
  exit 1
fi

# Install required Python dependencies (if requirements.txt exists)
if [ -f "requirements.txt" ]; then
  echo "Installing Python dependencies..."
  pip install -r requirements.txt
  if [ $? -ne 0 ]; then
    echo "Failed to install Python dependencies."
    deactivate
    exit 1
  fi
fi

# Navigate to the NPM directory
if [ ! -d "$NPM_DIR" ]; then
  echo "Error: NPM directory $NPM_DIR not found."
  exit 1
fi
cd "$NPM_DIR"

# Check if Node.js and npm are installed
if ! command_exists "npm"; then
  echo "Error: npm is not installed. Please install it and try again."
  exit 1
fi

# Install npm dependencies
if [ -f "package.json" ]; then
  echo "Installing npm dependencies..."
  npm install
  if [ $? -ne 0 ]; then
    echo "Failed to install npm dependencies."
    exit 1
  fi
fi

# Running API
cd libs_py
uvicorn api:app --host 0.0.0.0 --port 8001 &
if [$? -ne 0]; then
  echo "Failed to start API"
  exit 1
fi

# Go back to npm dir
cd ..

# Run the npm project
echo "Starting the npm project..."
npm run dev
if [ $? -ne 0 ]; then
  echo "Failed to start the npm project."
  exit 1
fi

# Done
echo "Script executed successfully."


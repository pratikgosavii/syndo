#!/bin/bash

# Script to run reminder checks on Linux VPS
# Make sure to set the correct path to your project directory

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment if it exists (uncomment and adjust path if needed)
# source /path/to/venv/bin/activate

# Run the management command
python manage.py check_reminders

# Optional: If you want to log output to a file
# python manage.py check_reminders >> logs/reminders.log 2>&1

# Deactivate virtual environment if activated
# deactivate


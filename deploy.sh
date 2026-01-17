#!/bin/bash

# Deployment script for Syndo
# This script handles git pull, migrations, and service restart
# Usage: ./deploy.sh

set -e  # Exit on error

echo "=========================================="
echo "Starting deployment..."
echo "=========================================="

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Stash any local changes (saves them in case you need them later)
echo "Stashing any local changes..."
git stash push -m "Auto-stash before deployment $(date +%Y-%m-%d_%H:%M:%S)" || echo "No changes to stash"

# Pull latest changes from master
echo "Pulling latest changes from origin/master..."
git pull origin master

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files (if needed)
echo "Collecting static files..."
python manage.py collectstatic --noinput || echo "Static files collection skipped or failed"

# Restart the service
echo "Restarting syndo service..."
systemctl restart syndo || echo "Service restart command failed - you may need to restart manually"

# Show status
echo "Checking service status..."
systemctl status syndo --no-pager -l || echo "Could not check service status"

echo "=========================================="
echo "Deployment completed!"
echo "=========================================="
echo ""
echo "Note: If you had local changes, they were stashed."
echo "To view stashed changes: git stash list"
echo "To restore stashed changes: git stash pop"


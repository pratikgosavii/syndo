#!/bin/bash
# Setup cron job to run reminders daily at midnight IST (12:00 AM)

# Get current directory
PROJECT_DIR=$(pwd)
echo "Project directory: $PROJECT_DIR"

# Get Python path
PYTHON_PATH=$(which python3)
if [ -z "$PYTHON_PATH" ]; then
    PYTHON_PATH=$(which python)
fi
echo "Python path: $PYTHON_PATH"

# Create logs directory if it doesn't exist
mkdir -p logs
touch logs/reminders.log

# Cron command: Run daily at midnight (00:00)
CRON_CMD="0 0 * * * cd $PROJECT_DIR && $PYTHON_PATH manage.py check_reminders >> $PROJECT_DIR/logs/reminders.log 2>&1"

# Remove any existing check_reminders cron job and add new one
(crontab -l 2>/dev/null | grep -v "check_reminders"; echo "$CRON_CMD") | crontab -

echo ""
echo "✓ Cron job added successfully!"
echo ""
echo "Schedule: Daily at midnight (12:00 AM)"
echo ""
echo "Cron job details:"
crontab -l | grep check_reminders
echo ""
echo "Note: Make sure your server timezone is set to IST (Asia/Kolkata)"
echo "To check timezone: timedatectl"
echo "To change timezone: sudo timedatectl set-timezone Asia/Kolkata"
echo ""
echo "To verify cron job: crontab -l"
echo "To view logs: tail -f $PROJECT_DIR/logs/reminders.log"


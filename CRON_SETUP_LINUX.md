# Cron Job Setup for Linux VPS

## Step 1: Make the Script Executable

```bash
chmod +x run_reminders.sh
```

## Step 2: Test the Script Manually

First, test that the script works:

```bash
# Navigate to your project directory
cd /var/www/syndo  # or wherever your project is located

# Test the script
./run_reminders.sh
```

If you're using a virtual environment, edit the script and uncomment the activate/deactivate lines, then update the path.

## Step 3: Set Up Logging Directory (Optional but Recommended)

```bash
mkdir -p logs
touch logs/reminders.log
chmod 666 logs/reminders.log  # Make sure it's writable
```

## Step 4: Add to Crontab

### Option A: Edit Crontab Directly

```bash
crontab -e
```

### Option B: Add Using Command Line

```bash
# First, find the path to your project
pwd  # Copy this path

# Add the cron job (replace /path/to/syndo with your actual path)
(crontab -l 2>/dev/null; echo "0 9 * * * cd /path/to/syndo && /usr/bin/python manage.py check_reminders >> /path/to/syndo/logs/reminders.log 2>&1") | crontab -
```

## Recommended Cron Schedule

### Daily at Midnight IST (12:00 AM) - RECOMMENDED
```bash
0 0 * * * cd /path/to/syndo && /usr/bin/python manage.py check_reminders >> /path/to/syndo/logs/reminders.log 2>&1
```

**Note:** Make sure your server timezone is set to IST. Check with `timedatectl`. If not, set it with:
```bash
sudo timedatectl set-timezone Asia/Kolkata
```

### Daily at 9:00 AM
```bash
0 9 * * * cd /path/to/syndo && /usr/bin/python manage.py check_reminders >> /path/to/syndo/logs/reminders.log 2>&1
```

### Every Hour During Business Hours (9 AM - 6 PM)
```bash
0 9-18 * * * cd /path/to/syndo && /usr/bin/python manage.py check_reminders >> /path/to/syndo/logs/reminders.log 2>&1
```

### Twice Daily (9 AM and 6 PM)
```bash
0 9,18 * * * cd /path/to/syndo && /usr/bin/python manage.py check_reminders >> /path/to/syndo/logs/reminders.log 2>&1
```

### Every 6 Hours
```bash
0 */6 * * * cd /path/to/syndo && /usr/bin/python manage.py check_reminders >> /path/to/syndo/logs/reminders.log 2>&1
```

## Cron Syntax Explained

```
* * * * * command
│ │ │ │ │
│ │ │ │ └─── Day of week (0-7, where 0 and 7 = Sunday)
│ │ │ └───── Month (1-12)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23)
└─────────── Minute (0-59)
```

## Using Virtual Environment

If you're using a virtual environment, use the Python from the venv:

```bash
# Example with virtual environment
0 9 * * * cd /path/to/syndo && /path/to/syndo/venv/bin/python manage.py check_reminders >> /path/to/syndo/logs/reminders.log 2>&1
```

Or use the shell script (which handles venv activation):

```bash
0 9 * * * /path/to/syndo/run_reminders.sh >> /path/to/syndo/logs/reminders.log 2>&1
```

## Finding Python Path

If you're not sure which Python to use:

```bash
# Check which Python Django uses
which python
# or
which python3

# Check Python version
python --version
# or
python3 --version
```

## Complete Setup Example

Here's a complete example assuming your project is at `/var/www/syndo`:

```bash
# 1. Navigate to project
cd /var/www/syndo

# 2. Make script executable
chmod +x run_reminders.sh

# 3. Create logs directory
mkdir -p logs
touch logs/reminders.log

# 4. Test the command manually first
python manage.py check_reminders

# 5. Add to crontab
crontab -e

# 6. Add this line (daily at 9 AM):
0 9 * * * cd /var/www/syndo && /usr/bin/python3 manage.py check_reminders >> /var/www/syndo/logs/reminders.log 2>&1

# 7. Save and exit (in vi: press Esc, type :wq, press Enter)
# (in nano: Ctrl+X, then Y, then Enter)
```

## Verify Cron Job

### Check if cron job was added:
```bash
crontab -l
```

### Check cron service is running:
```bash
# For systemd (most modern Linux)
sudo systemctl status cron

# For older systems
sudo service cron status
```

### View cron logs:
```bash
# Check syslog for cron entries
grep CRON /var/log/syslog

# Or check auth log
grep CRON /var/log/auth.log
```

## Troubleshooting

### Script doesn't run:
1. Check Python path is correct: `which python` or `which python3`
2. Check file permissions: `ls -la run_reminders.sh`
3. Check cron logs: `grep CRON /var/log/syslog | tail -20`
4. Make sure paths in cron are absolute (not relative)

### Permission errors:
```bash
# Make sure the logs directory is writable
chmod 755 logs
chmod 666 logs/reminders.log
```

### Python not found:
- Use full path to Python in cron
- Example: `/usr/bin/python3` instead of just `python`

### Django not found:
- Make sure you're in the project directory (use `cd` in cron command)
- Or activate virtual environment properly

### Email notifications:
If you want email notifications when the script runs, add your email:
```bash
MAILTO=your-email@example.com
0 9 * * * cd /path/to/syndo && python manage.py check_reminders >> logs/reminders.log 2>&1
```

## Monitoring

### View recent reminder check logs:
```bash
tail -f logs/reminders.log
```

### Count reminders created:
```bash
# In Django shell
python manage.py shell
>>> from vendor.models import Reminder
>>> Reminder.objects.count()
>>> Reminder.objects.filter(created_at__gte=timezone.now().replace(hour=0, minute=0, second=0)).count()
```

## Security Notes

- Make sure your logs directory has proper permissions
- Consider rotating logs to prevent them from growing too large
- Don't store sensitive information in cron logs


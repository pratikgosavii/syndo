# Quick Setup: Daily Reminder Check at Midnight IST (12:00 AM)

## Quick Setup (Automated)

Run this script to automatically set up the cron job:

```bash
chmod +x setup_midnight_cron.sh
./setup_midnight_cron.sh
```

## Manual Setup

### Step 1: Navigate to Your Project Directory

```bash
cd /var/www/syndo  # or your project path
```

### Step 2: Verify Timezone is IST

```bash
# Check current timezone
timedatectl

# If not IST, set it to IST
sudo timedatectl set-timezone Asia/Kolkata



# Verify
timedatectl
```

### Step 3: Test the Command Manually

```bash
python manage.py check_reminders
```

### Step 4: Add Cron Job

Edit crontab:
```bash
crontab -e
```

Add this line (replace `/var/www/syndo` with your actual project path):

```bash
0 0 * * * cd /var/www/syndo && /usr/bin/python3 manage.py check_reminders >> /var/www/syndo/logs/reminders.log 2>&1
```

**If using virtual environment**, use the Python from venv:
```bash
0 0 * * * cd /var/www/syndo && /var/www/syndo/venv/bin/python manage.py check_reminders >> /var/www/syndo/logs/reminders.log 2>&1
```

### Step 5: Save and Verify

- **vi/vim**: Press `Esc`, type `:wq`, press `Enter`
- **nano**: Press `Ctrl+X`, then `Y`, then `Enter`

Verify the cron job was added:
```bash
crontab -l
```

You should see:
```
0 0 * * * cd /var/www/syndo && /usr/bin/python3 manage.py check_reminders >> /var/www/syndo/logs/reminders.log 2>&1
```

## One-Line Command Setup

Replace `/var/www/syndo` and `/usr/bin/python3` with your paths:

```bash
(crontab -l 2>/dev/null | grep -v "check_reminders"; echo "0 0 * * * cd /var/www/syndo && /usr/bin/python3 manage.py check_reminders >> /var/www/syndo/logs/reminders.log 2>&1") | crontab -
```

## Verify It's Working

### Check cron service is running:
```bash
sudo systemctl status cron
# or
sudo service cron status
```

### View cron logs:
```bash
# Check if cron is executing
grep CRON /var/log/syslog | tail -20

# View reminder check logs
tail -f /var/www/syndo/logs/reminders.log
```

### Test immediately (without waiting for midnight):

Run the command manually to test:
```bash
python manage.py check_reminders
```

## Cron Schedule Breakdown

```
0 0 * * *
│ │ │ │ │
│ │ │ │ └─── Day of week (0-7, where 0 and 7 = Sunday)
│ │ │ └───── Month (1-12)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23) - 0 = midnight
└─────────── Minute (0-59) - 0 = on the hour
```

So `0 0 * * *` means:
- Minute: 0 (at the top of the hour)
- Hour: 0 (midnight/12:00 AM)
- Every day of the month
- Every month
- Every day of the week

## Troubleshooting

### Script doesn't run at midnight:

1. **Check timezone:**
   ```bash
   timedatectl
   date
   ```
   Should show IST timezone.

2. **Check cron is running:**
   ```bash
   sudo systemctl status cron
   ```

3. **Check cron logs:**
   ```bash
   grep CRON /var/log/syslog | grep check_reminders
   ```

4. **Check file permissions:**
   ```bash
   ls -la manage.py
   ls -la logs/reminders.log
   ```

### Timezone Issues:

If your server is in UTC but you want IST:
- **Option 1 (Recommended)**: Set server timezone to IST
  ```bash
  sudo timedatectl set-timezone Asia/Kolkata
  ```
  Then use: `0 0 * * *` (midnight IST)

- **Option 2**: Keep UTC and adjust the hour
  - IST is UTC+5:30, so midnight IST = 18:30 UTC (previous day)
  - Use: `30 18 * * *` (for UTC timezone)

### Python Path Issues:

Find the correct Python path:
```bash
which python3
which python
```

Use the full path in cron:
```bash
/usr/bin/python3  # instead of just python3
```

### Permission Issues:

Make sure the logs directory is writable:
```bash
mkdir -p logs
chmod 755 logs
touch logs/reminders.log
chmod 666 logs/reminders.log
```

## Monitoring

### View recent reminder checks:
```bash
tail -20 logs/reminders.log
```

### Watch logs in real-time:
```bash
tail -f logs/reminders.log
```

### Count reminders created today:
```bash
python manage.py shell
>>> from vendor.models import Reminder
>>> from django.utils import timezone
>>> Reminder.objects.filter(created_at__date=timezone.now().date()).count()
```

## Example Complete Setup Session

```bash
# 1. Navigate to project
cd /var/www/syndo

# 2. Set timezone to IST
sudo timedatectl set-timezone Asia/Kolkata

# 3. Verify timezone
timedatectl

# 4. Test command
python manage.py check_reminders

# 5. Create logs directory
mkdir -p logs
touch logs/reminders.log

# 6. Find Python path
which python3
# Output: /usr/bin/python3

# 7. Add cron job
crontab -e
# Add: 0 0 * * * cd /var/www/syndo && /usr/bin/python3 manage.py check_reminders >> /var/www/syndo/logs/reminders.log 2>&1

# 8. Verify
crontab -l

# 9. Check cron service
sudo systemctl status cron
```

Done! The script will now run daily at midnight IST (12:00 AM).


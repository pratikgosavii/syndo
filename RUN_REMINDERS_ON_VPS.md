# How to Run Reminder Script Manually on VPS

## Quick Command

```bash
python3 manage.py check_reminders
```

## Step-by-Step Instructions

### Step 1: SSH into Your VPS

```bash
ssh root@your-vps-ip
# or
ssh username@your-vps-ip
```

Replace `your-vps-ip` with your actual VPS IP address or hostname.

### Step 2: Navigate to Project Directory

```bash
cd /var/www/syndo
# or wherever your project is located
```

Based on your error logs, the project seems to be at `/var/www/syndo/`

### Step 3: Activate Virtual Environment (if using one)

```bash
source venv/bin/activate
# or
source /var/www/syndo/venv/bin/activate
```

You should see `(venv)` prefix in your terminal prompt.

### Step 4: Run the Reminder Check Script

```bash
python3 manage.py check_reminders
```

Or if using virtual environment's Python directly:

```bash
./venv/bin/python manage.py check_reminders
```

### Step 5: Check Output

You should see output like:

```
Starting reminder checks...
Successfully processed reminders. Total reminders created: X
```

## Alternative Methods

### Method 1: Run with Full Path

```bash
/var/www/syndo/venv/bin/python /var/www/syndo/manage.py check_reminders
```

This works even if you're not in the project directory.

### Method 2: Save Output to Log File

```bash
cd /var/www/syndo
source venv/bin/activate
python3 manage.py check_reminders >> logs/reminders.log 2>&1
```

The `2>&1` redirects both standard output and errors to the log file.

### Method 3: Run in Background

```bash
cd /var/www/syndo
source venv/bin/activate
nohup python3 manage.py check_reminders >> logs/reminders.log 2>&1 &
```

The `nohup` command allows it to continue running even if you disconnect from SSH.

### Method 4: Run with Verbose Output

```bash
python3 manage.py check_reminders --verbosity 2
```

This shows more detailed output for debugging.

## Complete Example Session

```bash
# 1. SSH into VPS
ssh root@srv1189647

# 2. Navigate to project
cd /var/www/syndo

# 3. Activate virtual environment
source venv/bin/activate

# 4. Run the script
python3 manage.py check_reminders

# Expected output:
# Starting reminder checks...
# Successfully processed reminders. Total reminders created: 5
```

## Troubleshooting

### Error: "command not found: python3"

Try using `python` instead:

```bash
python manage.py check_reminders
```

### Error: "No module named 'django'"

Make sure you're in the virtual environment:

```bash
source venv/bin/activate
```

Or use the virtual environment's Python directly:

```bash
./venv/bin/python manage.py check_reminders
```

### Error: "manage.py not found"

Make sure you're in the project root directory:

```bash
cd /var/www/syndo
ls manage.py  # Should list manage.py file
```

### Check Virtual Environment Location

If you're not sure where the virtual environment is:

```bash
# Find venv directory
find /var/www -name "activate" -type f 2>/dev/null

# Or check common locations
ls -la /var/www/syndo/venv/bin/activate
```

### Permission Issues

If you get permission errors:

```bash
# Check file permissions
ls -la manage.py

# Fix if needed (be careful with this)
chmod +x manage.py
```

## View Logs

After running, you can check the log file:

```bash
# View last 50 lines
tail -50 logs/reminders.log

# View entire log
cat logs/reminders.log

# Follow log in real-time (if running in background)
tail -f logs/reminders.log
```

## Test Run

To test if everything works:

```bash
cd /var/www/syndo
source venv/bin/activate
python3 manage.py check_reminders --verbosity 2
```

This will show detailed output of what the script is doing.


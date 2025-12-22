# How to Restart Django on Your VPS

## Check What's Running Django

First, find out how Django is currently running:

```bash
# Check if Django is running
ps aux | grep python
ps aux | grep gunicorn
ps aux | grep uwsgi

# Check what's listening on port 8000 (or your Django port)
sudo netstat -tlnp | grep :8000
# OR
sudo ss -tlnp | grep :8000
```

## Common Scenarios

### Scenario 1: Running with `python manage.py runserver` (Development)
If you're running it manually, just:
1. Stop it with `Ctrl+C`
2. Restart with: `python manage.py runserver 0.0.0.0:8000`

### Scenario 2: Running with Gunicorn (Production)
If gunicorn is running but not as a service:

```bash
# Find the gunicorn process
ps aux | grep gunicorn

# Kill the process (replace PID with actual process ID)
kill -HUP <PID>
# OR
pkill -HUP gunicorn

# Restart manually
gunicorn syndo.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

### Scenario 3: Running as Systemd Service
Check for different service names:

```bash
# Check all Django-related services
sudo systemctl list-units | grep -i django
sudo systemctl list-units | grep -i syndo
sudo systemctl list-units | grep -i python

# Common service names:
sudo systemctl restart django
sudo systemctl restart syndo
sudo systemctl restart python3
```

### Scenario 4: Running with Supervisor
If using supervisor:

```bash
sudo supervisorctl restart syndo
# OR
sudo supervisorctl restart gunicorn
```

### Scenario 5: Running in Screen/Tmux
If running in a screen or tmux session:

```bash
# List screen sessions
screen -ls

# Attach to session
screen -r <session-name>

# Inside screen: Ctrl+C to stop, then restart
python manage.py runserver
# OR
gunicorn syndo.wsgi:application --bind 0.0.0.0:8000
```

## Quick Restart Script

Create a simple restart script:

```bash
# Create restart script
nano restart_django.sh
```

Add this content:

```bash
#!/bin/bash
# Kill existing Django/gunicorn processes
pkill -f "python.*manage.py runserver"
pkill -f gunicorn

# Wait a moment
sleep 2

# Start Django (choose one method)

# Option 1: Development server
# python manage.py runserver 0.0.0.0:8000

# Option 2: Gunicorn (Production)
cd /var/www/syndo
source venv/bin/activate  # If using virtual environment
gunicorn syndo.wsgi:application --bind 0.0.0.0:8000 --workers 3 --daemon

echo "Django restarted!"
```

Make it executable:
```bash
chmod +x restart_django.sh
```

Run it:
```bash
./restart_django.sh
```

## After Restarting

1. **Verify it's running:**
   ```bash
   ps aux | grep python
   curl http://localhost:8000
   ```

2. **Check logs if there are errors:**
   ```bash
   tail -f logs/requests.log
   ```

3. **Test the upload limit fix:**
   - Try uploading a file > 10MB
   - Should now work up to 100MB

## Setting Up Gunicorn as a Service (Optional)

If you want to run gunicorn as a systemd service for easier management:

```bash
# Create service file
sudo nano /etc/systemd/system/syndo.service
```

Add this content:

```ini
[Unit]
Description=Syndo Django Application
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/var/www/syndo
Environment="PATH=/var/www/syndo/venv/bin"
ExecStart=/var/www/syndo/venv/bin/gunicorn syndo.wsgi:application --bind 0.0.0.0:8000 --workers 3
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable syndo

# Start service
sudo systemctl start syndo

# Check status
sudo systemctl status syndo

# Now you can restart with:
sudo systemctl restart syndo
```


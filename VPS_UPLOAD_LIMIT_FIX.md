# VPS Upload Limit Fix - Increase to 100MB

## Step 1: Find Your Web Server Configuration

First, check which web server you're using:

```bash
# Check if Nginx is running
sudo systemctl status nginx

# Check if Apache is running
sudo systemctl status apache2
```

---

## Step 2: Fix Nginx Configuration (Most Common)

### Find Your Nginx Config File

```bash
# Usually located in one of these:
/etc/nginx/sites-available/your-site-name
/etc/nginx/sites-available/default
/etc/nginx/nginx.conf
```

### Edit the Configuration

```bash
# Replace 'your-site-name' with your actual site name
sudo nano /etc/nginx/sites-available/your-site-name
```

### Add/Update This Line

Find the `server {` block and add this line inside it:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # ✅ ADD THIS LINE - Increase upload size to 100MB
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://127.0.0.1:8000;  # or your Django port
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Static files
    location /static/ {
        alias /path/to/your/static/files/;
    }
    
    # Media files
    location /media/ {
        alias /path/to/your/media/files/;
    }
}
```

### Test and Restart Nginx

```bash
# Test the configuration for errors
sudo nginx -t

# If test passes, restart Nginx
sudo systemctl restart nginx

# Check status
sudo systemctl status nginx
```

---

## Step 3: Fix Apache Configuration (If Using Apache)

### Edit Apache Config

```bash
sudo nano /etc/apache2/apache2.conf
# OR
sudo nano /etc/apache2/sites-available/your-site.conf
```

### Add This Line

```apache
# Increase upload size to 100MB (104857600 bytes)
LimitRequestBody 104857600
```

### Restart Apache

```bash
sudo systemctl restart apache2
sudo systemctl status apache2
```

---

## Step 4: Verify Django Settings

Your Django settings are already configured correctly:

```python
# In syndo/settings.py (already set)
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB
```

**Make sure to restart your Django server after any settings changes:**

```bash
# If using systemd service
sudo systemctl restart your-django-service

# If using gunicorn
sudo systemctl restart gunicorn

# If running manually
# Stop (Ctrl+C) and restart:
python manage.py runserver
# OR
gunicorn syndo.wsgi:application --bind 0.0.0.0:8000
```

---

## Step 5: Quick Test

After making changes, test with a file larger than 10MB:

1. Try uploading a reel file between 10-100MB
2. Check if it uploads successfully
3. If it still fails, check the error logs:

```bash
# Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Django logs
tail -f logs/requests.log
```

---

## Common Issues

### Issue: "413 Request Entity Too Large"
**Solution:** This means Nginx/Apache limit is still too low. Make sure you:
1. Added `client_max_body_size 100M;` in Nginx
2. Restarted Nginx/Apache
3. Cleared browser cache

### Issue: Changes Not Taking Effect
**Solution:**
1. Make sure you edited the correct config file
2. Restarted the web server
3. Restarted Django server
4. Check if there are multiple config files (sites-available vs sites-enabled)

### Issue: Can't Find Config File
**Solution:**
```bash
# List all Nginx config files
sudo find /etc/nginx -name "*.conf"

# List enabled sites
ls -la /etc/nginx/sites-enabled/
```

---

## Complete Example: Nginx Config for Django

Here's a complete example configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # ✅ CRITICAL: Increase upload size
    client_max_body_size 100M;
    
    # Increase timeouts for large uploads
    proxy_read_timeout 300s;
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /var/www/syndo/static/;
    }
    
    location /media/ {
        alias /var/www/syndo/media/;
    }
}
```

---

## After Making Changes

1. ✅ Test Nginx config: `sudo nginx -t`
2. ✅ Restart Nginx: `sudo systemctl restart nginx`
3. ✅ Restart Django: Restart your Django service
4. ✅ Test upload: Try uploading a file > 10MB

---

## Need Help?

If you're still having issues, check:
- Which web server you're using (Nginx or Apache)
- The exact error message you're getting
- Your VPS provider's documentation (some have additional limits)


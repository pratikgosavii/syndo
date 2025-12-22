# Troubleshooting 413 Error After Adding client_max_body_size

## Step 1: Verify Nginx Config Was Saved Correctly

```bash
# Check if the line was actually added
grep -r "client_max_body_size" /etc/nginx/

# Should show output like:
# /etc/nginx/sites-available/default:    client_max_body_size 100M;
```

## Step 2: Check for Syntax Errors

```bash
# Test Nginx configuration
sudo nginx -t

# If there are errors, fix them first
```

## Step 3: Make Sure You Edited the CORRECT File

Nginx uses files from `sites-enabled/`, not `sites-available/`:

```bash
# Check which config is actually being used
ls -la /etc/nginx/sites-enabled/

# The file in sites-enabled is usually a symlink to sites-available
# Make sure you edit the file that's actually linked/enabled
```

**Important:** If you edited `/etc/nginx/sites-available/default` but the enabled site is different, edit the enabled one:

```bash
# See what's enabled
cat /etc/nginx/sites-enabled/*

# Edit the actual enabled config
sudo nano /etc/nginx/sites-enabled/default
# OR
sudo nano /etc/nginx/sites-enabled/your-site-name
```

## Step 4: Check Main Nginx Config

Sometimes the limit needs to be in the main config file:

```bash
# Check main nginx.conf
sudo nano /etc/nginx/nginx.conf

# Add this in the http { block (not server block):
http {
    # Add this line
    client_max_body_size 100M;
    
    # ... rest of config
}
```

## Step 5: Verify Nginx Actually Restarted

```bash
# Check Nginx status
sudo systemctl status nginx

# Check if it's actually using the new config
sudo nginx -T | grep client_max_body_size

# Should show: client_max_body_size 100M;
```

## Step 6: Full Restart Sequence

```bash
# Stop Nginx
sudo systemctl stop nginx

# Test config
sudo nginx -t

# Start Nginx
sudo systemctl start nginx

# Check status
sudo systemctl status nginx
```

## Step 7: Check for Multiple Config Files

Sometimes there are multiple server blocks or includes:

```bash
# Find all nginx config files
sudo find /etc/nginx -name "*.conf" -type f

# Check if there are includes
grep -r "include" /etc/nginx/sites-enabled/
```

## Step 8: Clear Browser Cache

Sometimes browsers cache the error. Try:
- Hard refresh: Ctrl+Shift+R (or Cmd+Shift+R on Mac)
- Or use incognito/private mode
- Or try a different browser

## Step 9: Check Location Block

Make sure `client_max_body_size` is in the right place. It should be in the `server` block, but can also be in `location` blocks:

```nginx
server {
    # Global setting for entire server
    client_max_body_size 100M;
    
    location / {
        # Can also be set here for specific location
        # client_max_body_size 100M;
        proxy_pass http://127.0.0.1:8000;
    }
    
    # For media uploads specifically
    location /api/vendor/reel/ {
        client_max_body_size 100M;
        proxy_pass http://127.0.0.1:8000;
    }
}
```

## Step 10: Verify the Setting is Active

```bash
# Reload Nginx config (without stopping)
sudo nginx -s reload

# Check what Nginx is actually using
sudo nginx -T 2>/dev/null | grep -A 5 -B 5 "client_max_body_size"
```

## Common Mistakes

1. **Editing wrong file** - Edited `sites-available` but not the symlink in `sites-enabled`
2. **Syntax error** - Missing semicolon or wrong placement
3. **Not restarting** - Changed config but didn't restart/reload Nginx
4. **Browser cache** - Browser cached the 413 error
5. **Multiple server blocks** - Only added to one server block, but request goes to another

## Complete Example Config

Here's what your config should look like:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # ✅ THIS LINE MUST BE HERE
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
        
        # Can also set here if needed
        # client_max_body_size 100M;
    }
    
    location /static/ {
        alias /var/www/syndo/static/;
    }
    
    location /media/ {
        alias /var/www/syndo/media/;
    }
}
```

## Quick Diagnostic Commands

Run these to see what's happening:

```bash
# 1. Check if setting exists
sudo nginx -T 2>/dev/null | grep client_max_body_size

# 2. Check Nginx error log
sudo tail -20 /var/log/nginx/error.log

# 3. Check which config files are loaded
sudo nginx -T 2>/dev/null | head -20

# 4. Verify Nginx is running
sudo systemctl status nginx
```


# Reminder Script Execution Guide

## How to Run the Script

### 1. Manual Execution (Testing)

Run the command directly from your project directory:

```bash
# Windows (PowerShell/CMD)
python manage.py check_reminders

# Linux/Mac
python manage.py check_reminders
```

This will:
- Check all vendors/users with ReminderSetting configured
- Create reminders based on their settings
- Display the total number of reminders created

---

## 2. Automated Scheduling Options

### Option A: Windows Task Scheduler (Recommended for Windows)

Since you're on Windows, use Task Scheduler:

1. **Open Task Scheduler**:
   - Press `Win + R`, type `taskschd.msc`, press Enter

2. **Create Basic Task**:
   - Click "Create Basic Task" in the right panel
   - Name: "Check Reminders"
   - Description: "Run reminder checks for vendors"

3. **Set Trigger**:
   - Choose "Daily" (recommended) or "Hourly"
   - Set time: e.g., 9:00 AM daily

4. **Set Action**:
   - Action: "Start a program"
   - Program/script: `python` (or full path: `C:\Python\python.exe`)
   - Add arguments: `manage.py check_reminders`
   - Start in: `C:\Users\Pratik Gosavi\OneDrive\Desktop\hope again\syndo`

5. **Save and Test**:
   - Run the task manually to test
   - Check logs/console output

**PowerShell Script** (alternative approach):
Create a file `run_reminders.ps1`:
```powershell
cd "C:\Users\Pratik Gosavi\OneDrive\Desktop\hope again\syndo"
python manage.py check_reminders
```

Then schedule this PowerShell script in Task Scheduler.

---

### Option B: Cron Job (Linux/Mac/Production Server)

For production servers running Linux, add to crontab:

```bash
# Edit crontab
crontab -e

# Run daily at 9:00 AM
0 9 * * * cd /path/to/syndo && /usr/bin/python manage.py check_reminders >> /var/log/reminders.log 2>&1

# Or run every hour
0 * * * * cd /path/to/syndo && /usr/bin/python manage.py check_reminders >> /var/log/reminders.log 2>&1
```

---

### Option C: Django Management Command via API Endpoint (Manual Trigger)

Create an API endpoint that triggers the command:

Add to `vendor/views.py`:
```python
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.management import call_command
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@require_http_methods(["POST"])
def trigger_reminder_check(request):
    """API endpoint to manually trigger reminder checks"""
    try:
        call_command('check_reminders')
        return JsonResponse({'status': 'success', 'message': 'Reminder check completed'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
```

Add to `vendor/urls.py`:
```python
path('admin/trigger-reminders/', views.trigger_reminder_check, name='trigger_reminders'),
```

---

## Recommended Schedule

### Daily Execution (Recommended)
- **Time**: 9:00 AM (before business hours)
- **Why**: Check overnight changes, prepare for the day
- **Frequency**: Once per day

### Hourly Execution (For Critical Reminders)
- **Time**: Every hour during business hours (9 AM - 6 PM)
- **Why**: Get real-time updates on urgent reminders
- **Frequency**: Multiple times per day

### Weekly Execution (For Low Priority)
- **Time**: Monday morning at 9:00 AM
- **Why**: Weekly summary of all reminders
- **Frequency**: Once per week

---

## Best Practices

1. **Start with Daily**: Run daily first, monitor the results, then adjust frequency if needed

2. **Log Output**: Always log output to a file for debugging:
   ```bash
   python manage.py check_reminders >> logs/reminders.log 2>&1
   ```

3. **Monitor Performance**: Check how long the script takes to run
   - If it takes too long, consider optimizing queries
   - Consider running during off-peak hours

4. **Error Handling**: The script already has error handling, but monitor logs for any issues

5. **Database Backup**: Ensure database backups are in place before automated runs

---

## Testing

Before setting up automation:

1. **Test manually first**:
   ```bash
   python manage.py check_reminders
   ```

2. **Check the output** - should see:
   - "Starting reminder checks..."
   - "Successfully processed reminders. Total reminders created: X"

3. **Verify in database**:
   ```python
   from vendor.models import Reminder
   Reminder.objects.all().count()  # Should show created reminders
   ```

4. **Check a specific user's reminders**:
   ```python
   from vendor.models import Reminder
   from users.models import User
   user = User.objects.first()
   Reminder.objects.filter(user=user).values('reminder_type', 'title', 'message')
   ```

---

## Troubleshooting

### Script doesn't run:
- Check Python path in Task Scheduler
- Verify Django environment is activated
- Check file paths are correct

### No reminders created:
- Verify users have ReminderSetting configured
- Check that reminder toggles are enabled
- Verify there's actual data (purchases, sales, products) to check

### Too many reminders:
- The script prevents duplicates (only creates if no existing unread reminder)
- Already handled in the code logic

---

## Next Steps

1. ✅ Run manually to test: `python manage.py check_reminders`
2. ✅ Verify reminders are created in database
3. ✅ Set up Windows Task Scheduler (or cron for Linux)
4. ✅ Monitor logs for first few days
5. ✅ Adjust schedule if needed


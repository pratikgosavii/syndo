#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'syndo.settings')
django.setup()

from users.models import User

# Get a user to test deletion (you can modify this to target a specific user)
print("Available users:")
users = User.objects.all()[:10]
for u in users:
    print(f"ID: {u.id}, Mobile: {u.mobile}, Email: {u.email}, Username: {u.username}")

# Ask for user ID or use first user
if len(sys.argv) > 1:
    user_id = int(sys.argv[1])
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        print(f"User with ID {user_id} not found!")
        sys.exit(1)
else:
    if users:
        user = users[0]
        print(f"\nUsing first user: ID={user.id}, Mobile={user.mobile}")
    else:
        print("No users found!")
        sys.exit(1)

print(f"\nAttempting to delete user ID={user.id}, Mobile={user.mobile}...")
print("-" * 60)

try:
    user.delete()
    print("User deleted successfully!")
except Exception as e:
    print(f"Error deleting user: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()


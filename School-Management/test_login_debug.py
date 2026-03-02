#!/usr/bin/env python
"""Test login with cache clearing"""
import sys
import os

# Add the app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app, Admin, clear_cache
from werkzeug.security import check_password_hash

print("=" * 70)
print("TESTING ADMIN LOGIN WITH CACHE CLEARED")
print("=" * 70)

# Clear all cache
print("\n🧹 Clearing cache...")
clear_cache()
print("   ✅ Cache cleared")

# Test login
print("\n🔍 Testing admin login...")
username = 'admin'
password = 'admin123'

print(f"   Looking for: {username}")
admin = Admin.find_by_username(username)

if admin:
    print(f"   ✅ Found admin: {admin.username}")
    
    is_valid = check_password_hash(admin.password_hash, password)
    print(f"   Checking password...")
    if is_valid:
        print(f"   ✅ Password is correct!")
        print(f"\n✅ LOGIN SUCCESS")
        print(f"   Admin ID: {admin.id}")
        print(f"   Username: {admin.username}")
        print(f"   Email: {admin.email}")
    else:
        print(f"   ❌ Password is WRONG")
else:
    print(f"   ❌ Admin '{username}' NOT FOUND in database")

print("\n" + "=" * 70)

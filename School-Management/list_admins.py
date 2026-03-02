#!/usr/bin/env python
"""List all admin users in database"""
import sqlite3
import json

conn = sqlite3.connect('school_management.db')
cursor = conn.cursor()

print("=" * 60)
print("EXISTING ADMIN USERS IN DATABASE")
print("=" * 60)

rows = cursor.execute('SELECT data FROM app_data WHERE collection="admin"').fetchall()

if not rows:
    print("\n❌ No admin users found in database!")
else:
    for idx, row in enumerate(rows, 1):
        admin = json.loads(row[0])
        print(f"\n{idx}. Username: {admin['username']}")
        print(f"   Email: {admin.get('email', 'N/A')}")
        print(f"   Created: {admin.get('created_at', 'N/A')}")

print("\n" + "=" * 60)
conn.close()

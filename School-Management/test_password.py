#!/usr/bin/env python
"""Test admin login"""
import sqlite3
import json
from werkzeug.security import check_password_hash

DATABASE = 'school_management.db'
conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

# Get admin data
rows = cursor.execute('SELECT data FROM app_data WHERE collection="admin" AND json_extract(data, "$.username") = ?', ('admin',)).fetchall()

if rows:
    admin = json.loads(rows[0][0])
    print("=" * 60)
    print("ADMIN PASSWORD TEST")
    print("=" * 60)
    print(f"Username: {admin['username']}")
    print(f"Email: {admin['email']}")
    print(f"Password Hash: {admin['password_hash'][:50]}...")
    
    test_password = 'admin123'
    is_valid = check_password_hash(admin['password_hash'], test_password)
    
    print(f"\nTesting password: '{test_password}'")
    print(f"Result: {'✅ VALID' if is_valid else '❌ INVALID'}")
    print("=" * 60)
else:
    print("❌ No admin found")

conn.close()

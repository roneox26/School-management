#!/usr/bin/env python
"""Test the login process"""
import sqlite3
import json
from werkzeug.security import check_password_hash

DATABASE = 'school_management.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def get_from_db(collection, data_id=None):
    """Get data from SQLite"""
    try:
        data = None
        with get_db_connection() as conn:
            if data_id:
                row = conn.execute(
                    "SELECT data FROM app_data WHERE collection = ? AND id = ?",
                    (collection, data_id)
                ).fetchone()
                if row:
                    data = json.loads(row['data'])
            else:
                rows = conn.execute(
                    "SELECT data FROM app_data WHERE collection = ?",
                    (collection,)
                ).fetchall()
                data = [json.loads(row['data']) for row in rows]

        return data if data_id else (data or [])
    except Exception as e:
        print(f"Error getting from DB: {e}")
        return None if data_id else []

def query_db(collection, **filters):
    """Query data with filters"""
    try:
        items = get_from_db(collection)
        if not items:
            return []

        filtered_items = []
        for item in items:
            if not item: continue
            match = True
            for key, value in filters.items():
                if key not in item or item[key] != value:
                    match = False
                    break
            if match:
                filtered_items.append(item)
        return filtered_items
    except Exception as e:
        print(f"Error querying DB: {e}")
        return []

# Test
print("=" * 60)
print("LOGIN TEST")
print("=" * 60)

username = 'admin'
password = 'admin123'

print(f"\n1️⃣  Looking for user: {username}")
admins = query_db('admin', username=username)
print(f"   Found {len(admins)} admin(s)")

if admins:
    admin = admins[0]
    print(f"\n2️⃣  Admin data:")
    print(f"   Username: {admin['username']}")
    print(f"   Email: {admin['email']}")
    
    print(f"\n3️⃣  Checking password...")
    is_valid = check_password_hash(admin['password_hash'], password)
    print(f"   Password '{password}': {'✅ VALID' if is_valid else '❌ INVALID'}")
    
    if is_valid:
        print(f"\n✅ LOGIN SUCCESS!")
    else:
        print(f"\n❌ LOGIN FAILED - Wrong password")
else:
    print(f"   ❌ User '{username}' not found in database")

print("=" * 60)

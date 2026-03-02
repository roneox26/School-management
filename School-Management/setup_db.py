#!/usr/bin/env python
"""Initialize database with admin user"""
import sqlite3
import json
import uuid
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash

DATABASE = 'school_management.db'

# Create connection
conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

print("=" * 70)
print("DATABASE INITIALIZATION")
print("=" * 70)

# Step 1: Create table if it doesn't exist
print("\n📋 Creating app_data table...")
try:
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS app_data (
            collection TEXT,
            id TEXT,
            data TEXT,
            PRIMARY KEY (collection, id)
        )
    ''')
    conn.commit()
    print("  ✅ Table created successfully")
except Exception as e:
    print(f"  ❌ Error: {e}")
    conn.close()
    exit(1)

# Step 2: Create admin user
print("\n👤 Creating admin user...")
try:
    admin_id = str(uuid.uuid4())
    admin_data = {
        'id': admin_id,
        'username': 'admin',
        'email': 'admin@school.com',
        'password_hash': generate_password_hash('admin123'),
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    cursor.execute(
        'INSERT INTO app_data (collection, id, data) VALUES (?, ?, ?)',
        ('admin', admin_id, json.dumps(admin_data))
    )
    conn.commit()
    print("  ✅ Admin user created")
    print(f"     Username: admin")
    print(f"     Password: admin123")
except Exception as e:
    print(f"  ❌ Error: {e}")
    conn.close()
    exit(1)

# Step 3: Verify
print("\n🔍 Verifying...")
try:
    rows = cursor.execute('SELECT data FROM app_data WHERE collection="admin"').fetchall()
    print(f"  ✅ Found {len(rows)} admin user(s)")
    for row in rows:
        admin = json.loads(row[0])
        print(f"     - {admin['username']}")
except Exception as e:
    print(f"  ❌ Error: {e}")

print("\n" + "=" * 70)
print("✅ DATABASE SETUP COMPLETE!")
print("=" * 70)
print("\n🔓 Login Credentials:")
print("   Username: admin")
print("   Password: admin123")
print("=" * 70 + "\n")

conn.close()

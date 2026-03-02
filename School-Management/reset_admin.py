#!/usr/bin/env python
"""
Reset Admin Password - Simple and Direct
Creates a fresh admin user with password: admin123
"""
import sqlite3
import json
import uuid
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash

# Database connection
DATABASE = 'school_management.db'
conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

print("=" * 70)
print("ADMIN PASSWORD RESET TOOL")
print("=" * 70)

# Step 1: Check current admin users
print("\n📋 Current admin users:")
rows = cursor.execute('SELECT data FROM app_data WHERE collection="admin"').fetchall()
for row in rows:
    admin = json.loads(row[0])
    print(f"  - {admin['username']} (Email: {admin.get('email', 'N/A')})")

# Step 2: Delete ALL existing admin users
print("\n🗑️  Removing old admin users...")
cursor.execute('DELETE FROM app_data WHERE collection="admin"')
conn.commit()
print("  ✅ Deleted all old admin users")

# Step 3: Create fresh admin user
print("\n👤 Creating new admin user...")

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

print(f"  ✅ Created admin user successfully!")
print(f"     Username: {admin_data['username']}")
print(f"     Password: admin123")
print(f"     Email: {admin_data['email']}")

# Step 4: Verify the creation
print("\n🔍 Verifying new admin user...")
rows = cursor.execute('SELECT data FROM app_data WHERE collection="admin"').fetchall()
if rows:
    admin = json.loads(rows[0][0])
    print(f"  ✅ Confirmed: User '{admin['username']}' exists in database")
else:
    print("  ❌ ERROR: Admin user not found!")

conn.close()

print("\n" + "=" * 70)
print("✅ ADMIN RESET COMPLETE!")
print("=" * 70)
print("\n🔓 Login with these credentials:")
print("   Username: admin")
print("   Password: admin123")
print("=" * 70)

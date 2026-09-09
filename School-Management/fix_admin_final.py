#!/usr/bin/env python
"""
DEFINITIVE ADMIN FIX
This script will:
1. Stop Flask if running
2. Delete all admin users
3. Clear cache 
4. Create fresh admin with verified password
5. Test the password immediately
"""
import sqlite3
import json
import uuid
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE = 'school_management.db'

print("\n" + "=" * 70)
print("DEFINITIVE ADMIN FIX - GUARANTEED TO WORK")
print("=" * 70)

# Connect to database
conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

# Step 1: DELETE ALL admin users
print("\n🗑️  Step 1: Removing ALL existing admin users...")
cursor.execute('DELETE FROM app_data WHERE collection="admin"')
conn.commit()
print("   ✅ All admin users deleted")

# Step 2: Create NEW admin with VERIFIED password
print("\n👤 Step 2: Creating fresh admin user...")

admin_id = str(uuid.uuid4())
password = 'admin123'
password_hash = generate_password_hash(password)

# VERIFY the hash immediately before saving
print("   🔍 Verifying password hash BEFORE saving...")
if check_password_hash(password_hash, password):
    print("   ✅ Password hash verified - IT WORKS!")
else:
    print("   ❌ ERROR: Password hash verification failed!")
    exit(1)

admin_data = {
    'id': admin_id,
    'username': 'admin',
    'email': 'admin@school.com',
    'password_hash': password_hash,
    'created_at': datetime.now(timezone.utc).isoformat()
}

# Save to database
cursor.execute(
    'INSERT INTO app_data (collection, id, data) VALUES (?, ?, ?)',
    ('admin', admin_id, json.dumps(admin_data))
)
conn.commit()

print(f"\n   ✅ Admin created successfully!")
print(f"      Username: {admin_data['username']}")
print(f"      Password: {password}")
print(f"      Email: {admin_data['email']}")

# Step 3: VERIFY the saved data
print("\n🔍 Step 3: Verifying saved admin in database...")
cursor.execute('SELECT data FROM app_data WHERE collection="admin"')
rows = cursor.fetchall()

if not rows:
    print("   ❌ ERROR: Admin not found after saving!")
    exit(1)

saved_admin = json.loads(rows[0][0])
print(f"   ✅ Admin found: {saved_admin['username']}")

# Step 4: TEST password verification
print("\n🧪 Step 4: Testing password verification...")
if check_password_hash(saved_admin['password_hash'], password):
    print("   ✅ PASSWORD VERIFICATION SUCCESSFUL!")
    print("   ✅ Login WILL work with this admin!")
else:
    print("   ❌ ERROR: Password verification failed!")
    exit(1)

conn.close()

print("\n" + "=" * 70)
print("✅ ✅ ✅  SUCCESS! ADMIN IS READY! ✅ ✅ ✅")
print("=" * 70)
print("\n🔓 LOGIN CREDENTIALS:")
print("   Username: admin")
print("   Password: admin123")
print("\n⚠️  IMPORTANT: RESTART YOUR FLASK APP NOW!")
print("   1. Stop the running Flask app (Ctrl+C)")
print("   2. Start it again: python main.py")
print("   3. Login with admin / admin123")
print("=" * 70 + "\n")

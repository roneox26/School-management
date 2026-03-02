#!/usr/bin/env python
"""
Complete Login Diagnostic Tool
Tests the entire login flow to find the issue
"""
import sqlite3
import json
from datetime import datetime, timezone
from werkzeug.security import check_password_hash, generate_password_hash

DATABASE = 'school_management.db'

print("=" * 70)
print("COMPLETE LOGIN DIAGNOSTIC")
print("=" * 70)

# Step 1: Check database connection
print("\n1️⃣ Testing database connection...")
try:
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    print("   ✅ Database connected successfully")
except Exception as e:
    print(f"   ❌ Database connection failed: {e}")
    exit(1)

# Step 2: List all admin users
print("\n2️⃣ Checking admin users in database...")
try:
    rows = cursor.execute('SELECT data FROM app_data WHERE collection="admin"').fetchall()
    print(f"   Found {len(rows)} admin user(s)")
    
    if len(rows) == 0:
        print("   ❌ NO ADMIN USERS FOUND!")
        print("   Creating admin user now...")
        
        import uuid
        from datetime import datetime
        
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
        print("   ✅ Admin user created!")
        
        # Re-fetch
        rows = cursor.execute('SELECT data FROM app_data WHERE collection="admin"').fetchall()
    
    for idx, row in enumerate(rows, 1):
        admin = json.loads(row[0])
        print(f"\n   Admin {idx}:")
        print(f"     Username: {admin['username']}")
        print(f"     Email: {admin.get('email', 'N/A')}")
        print(f"     Has password_hash: {bool(admin.get('password_hash'))}")
        print(f"     Password hash (first 50 chars): {admin.get('password_hash', '')[:50]}...")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

# Step 3: Test password verification
print("\n3️⃣ Testing password verification...")
try:
    test_username = 'admin'
    test_password = 'admin123'
    
    cursor.execute('SELECT data FROM app_data WHERE collection="admin"')
    found = False
    
    for row in cursor.fetchall():
        admin = json.loads(row[0])
        if admin['username'] == test_username:
            found = True
            password_hash = admin.get('password_hash')
            
            print(f"   Testing: {test_username} / {test_password}")
            print(f"   Password hash exists: {bool(password_hash)}")
            
            if password_hash:
                result = check_password_hash(password_hash, test_password)
                if result:
                    print(f"   ✅ PASSWORD VERIFIED! Login should work!")
                else:
                    print(f"   ❌ PASSWORD VERIFICATION FAILED!")
                    
                    # Try generating a fresh hash and testing
                    print(f"\n   Testing fresh hash generation...")
                    fresh_hash = generate_password_hash(test_password)
                    print(f"   Fresh hash: {fresh_hash[:50]}...")
                    fresh_result = check_password_hash(fresh_hash, test_password)
                    print(f"   Fresh hash verification: {'✅ PASS' if fresh_result else '❌ FAIL'}")
            else:
                print(f"   ❌ No password hash found!")
            break
    
    if not found:
        print(f"   ❌ User '{test_username}' not found in database!")
        
except Exception as e:
    print(f"   ❌ Error during verification: {e}")

# Step 4: Test the exact query used by login
print("\n4️⃣ Testing login query (simulating Flask login)...")
try:
    # This simulates what Admin.find_by_username does
    test_username = 'admin'
    
    cursor.execute('SELECT data FROM app_data WHERE collection="admin"')
    all_admins = [json.loads(row[0]) for row in cursor.fetchall()]
    
    # Filter by username (client-side like query_db does)
    matching_admins = [a for a in all_admins if a.get('username') == test_username]
    
    if matching_admins:
        admin = matching_admins[0]
        print(f"   ✅ Found admin via query: {admin['username']}")
        print(f"   Testing password check...")
        
        result = check_password_hash(admin['password_hash'], 'admin123')
        print(f"   Password check result: {'✅ VALID' if result else '❌ INVALID'}")
    else:
        print(f"   ❌ No admin found with username '{test_username}'")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

conn.close()

print("\n" + "=" * 70)
print("DIAGNOSTIC COMPLETE")
print("=" * 70)
print("\n💡 RECOMMENDED ACTION:")
print("   If password verification passed: Restart Flask app")
print("   If password verification failed: Run this script's admin creation")
print("=" * 70)

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Create or Reset Admin User
This script creates a new admin user with specified credentials
"""

import sqlite3
import json
import uuid
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash

def create_admin_user(username, password, email=None):
    """Create a new admin user in the database"""
    
    DATABASE = 'school_management.db'
    
    try:
        # Create admin data
        admin_data = {
            'id': str(uuid.uuid4()),
            'username': username,
            'email': email or f'{username}@school.com',
            'password_hash': generate_password_hash(password),
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Connect to database
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Check if admin already exists
        cursor.execute(
            "SELECT data FROM app_data WHERE collection = 'admin' AND json_extract(data, '$.username') = ?",
            (username,)
        )
        existing = cursor.fetchone()
        
        if existing:
            # Update existing admin
            existing_data = json.loads(existing[0])
            existing_data['password_hash'] = admin_data['password_hash']
            
            cursor.execute(
                "UPDATE app_data SET data = ? WHERE collection = 'admin' AND id = ?",
                (json.dumps(existing_data), existing_data['id'])
            )
            print(f"✅ Updated admin user: {username}")
            print(f"   Password has been reset to: {password}")
        else:
            # Create new admin
            cursor.execute(
                "INSERT INTO app_data (collection, id, data) VALUES (?, ?, ?)",
                ('admin', admin_data['id'], json.dumps(admin_data))
            )
            print(f"✅ Created new admin user: {username}")
            print(f"   Password: {password}")
        
        conn.commit()
        conn.close()
        
        return True, admin_data
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False, None

if __name__ == '__main__':
    print("=" * 50)
    print("Admin User Creation Tool")
    print("=" * 50)
    
    # Create default admin users
    print("\n1. Creating/Updating 'admin' user...")
    create_admin_user('admin', 'admin123', 'admin@school.com')
    
    print("\n2. Creating/Updating 'admin' user with password 'admin'...")
    create_admin_user('admin2', 'admin', 'admin2@school.com')
    
    print("\n3. Creating/Updating '7' user...")
    create_admin_user('7', 'pass', '7@school.com')
    
    print("\n" + "=" * 50)
    print("✅ Admin users created/updated successfully!")
    print("=" * 50)
    print("\nYou can now login with:")
    print("  Username: admin")
    print("  Password: admin123")
    print("\nOR")
    print("  Username: 7")
    print("  Password: pass")
    print("=" * 50)

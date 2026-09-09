#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick Admin Password Test
Tests if the admin password works
"""

from werkzeug.security import check_password_hash
import sqlite3
import json

DATABASE = 'school_management.db'

def test_login(username, password):
    """Test if login credentials work"""
    
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Find admin user
        cursor.execute(
            "SELECT data FROM app_data WHERE collection = 'admin'"
        )
        
        admin_found = False
        for row in cursor.fetchall():
            admin_data = json.loads(row[0])
            
            if admin_data['username'] == username:
                admin_found = True
                password_hash = admin_data['password_hash']
                
                if check_password_hash(password_hash, password):
                    print(f"✅ SUCCESS! Login works for: {username}")
                    print(f"   Password: {password}")
                    return True
                else:
                    print(f"❌ FAILED! Wrong password for: {username}")
                    print(f"   Tried password: {password}")
                    return False
        
        if not admin_found:
            print(f"❌ User '{username}' not found in database")
            return False
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == '__main__':
    print("=" * 50)
    print("Testing Admin Credentials")
    print("=" * 50)
    
    print("\n1. Testing: admin / admin123")
    test_login('admin', 'admin123')
    
    print("\n2. Testing: admin / admin")
    test_login('admin', 'admin')
    
    print("\n3. Testing: 7 / pass")
    test_login('7', 'pass')
    
    print("\n" + "=" * 50)

#!/usr/bin/env python
"""Test login with proper CSRF token"""
import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app

print("=" * 70)
print("TESTING FLASK LOGIN WITH CSRF TOKEN")
print("=" * 70)

with app.test_client() as client:
    # Step 1: Get login page to extract CSRF token
    print("\n1️⃣  Getting CSRF token from login page...")
    response = client.get('/login')
    
    # Extract CSRF token from form
    csrf_match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', response.data.decode())
    if csrf_match:
        csrf_token = csrf_match.group(1)
        print(f"   ✅ CSRF token found: {csrf_token[:20]}...")
    else:
        print("   ⚠️  No CSRF token found in form")
        csrf_token = None
    
    # Step 2: Login with correct credentials
    print("\n2️⃣  Attempting login...")
    response = client.post('/login', data={
        'username': 'admin',
        'password': 'admin123',
        'csrf_token': csrf_token
    }, follow_redirects=True)
    
    print(f"   Status: {response.status_code}")
    
    # Check if login was successful
    if b'Invalid username or password' in response.data:
        print("   ❌ FAILED: 'Invalid username or password' error")
    elif b'dashboard' in response.data or b'Dashboard' in response.data or b'students' in response.data:
        print("   ✅ SUCCESS: Logged in successfully!")
    else:
        print("   ⚠️  Unknown response")
    
    # Step 3: Try accessing dashboard to verify authentication
    print("\n3️⃣  Checking if session is authenticated...")
    response = client.get('/dashboard')
    
    if response.status_code == 200:
        print("   ✅ Dashboard is accessible - authentication works!")
    elif response.status_code == 302:
        print("   ❌ Redirected to login - not authenticated")
    else:
        print(f"   ⚠️  Status: {response.status_code}")

print("\n" + "=" * 70)

#!/usr/bin/env python
"""Test login with debug output"""
import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app

print("=" * 70)
print("TESTING LOGIN WITH DEBUG OUTPUT")
print("=" * 70)

with app.test_client() as client:
    print("\n[STEP 1] Getting login form and CSRF token...")
    response = client.get('/login')
    
    # Extract CSRF token
    csrf_match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', response.data.decode())
    csrf_token = csrf_match.group(1) if csrf_match else None
    
    print("[STEP 2] Submitting login form...")
    print("   Username: admin")
    print("   Password: admin123")
    
    response = client.post('/login', data={
        'username': 'admin',
        'password': 'admin123',
        'csrf_token': csrf_token
    }, follow_redirects=True)
    
    print(f"\n[RESULT] Response status: {response.status_code}")
    
    # Check for errors
    response_text = response.data.decode()
    if 'Invalid username or password' in response_text:
        print("[ERROR] 'Invalid username or password' shown to user")
    elif 'Dashboard' in response_text or 'dashboard' in response_text:
        print("[SUCCESS] User logged in to dashboard")
    else:
        print("[INFO] Unknown response")
    
    # Check if dashboard is accessible
    print("\n[STEP 3] Verifying dashboard access...")
    response = client.get('/dashboard')
    if response.status_code == 200:
        print("[SUCCESS] Dashboard is accessible")
    else:
        print(f"[ERROR] Dashboard not accessible (status: {response.status_code})")

print("\n" + "=" * 70)

#!/usr/bin/env python
"""Test Flask app login route"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app

print("=" * 70)
print("TESTING FLASK APP LOGIN")
print("=" * 70)

# Create test client
with app.test_client() as client:
    print("\n1️⃣  Testing GET /login...")
    response = client.get('/login')
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ GET /login works")
    else:
        print(f"   ❌ Error: {response.status_code}")
    
    print("\n2️⃣  Testing POST /login with credentials...")
    response = client.post('/login', data={
        'username': 'admin',
        'password': 'admin123',
        'csrf_token': None  # Will need to get from form
    }, follow_redirects=True)
    
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        if b'dashboard' in response.data or b'student' in response.data:
            print("   ✅ Login successful - redirected to dashboard")
        else:
            print("   ⚠️  Response received but not dashboard")
            # Print first 500 chars of response
            print(f"   Response preview: {response.data[:500]}")
    else:
        print(f"   ❌ Error: {response.status_code}")

print("\n" + "=" * 70)

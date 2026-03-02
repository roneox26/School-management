#!/usr/bin/env python
"""Simple test to verify app can start"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app

print("=" * 70)
print("STARTING FLASK APP")
print("=" * 70)
print("\n[INFO] Flask app initialized successfully!")
print("[INFO] Running on: http://localhost:5000")
print("[INFO] Credentials: admin / admin123")
print("[INFO] Press Ctrl+C to stop\n")
print("=" * 70 + "\n")

try:
    app.run(debug=True, port=5000, host='0.0.0.0')
except KeyboardInterrupt:
    print("\n\n[INFO] Server stopped")

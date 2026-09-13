"""
Flask application entry point for Render deployment.
"""
import os
import sys

# Ensure current directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Flask app and initialization
from main import app, init_app, get_from_db

print("[APP] Starting Flask application...")
print(f"[APP] DATABASE_URL: {'SET' if os.environ.get('DATABASE_URL') else 'NOT SET'}")

# Initialize database and create default admin
try:
    print("[APP] Calling init_app()...")
    init_app()
    print("[APP] init_app() completed successfully")
    
    # Verify admin was created
    admins = get_from_db('admin')
    if isinstance(admins, list):
        print(f"[APP] Admin users in database: {len(admins)}")
        if len(admins) > 0:
            print(f"[APP] Default admin username: {admins[0].get('username')}")
    else:
        print("[APP] No admins found in database")
except Exception as e:
    print(f"[APP] ERROR during init_app(): {str(e)}")
    import traceback
    traceback.print_exc()

print("[APP] Flask app ready to handle requests")

# This is what gunicorn will call
if __name__ == "__main__":
    app.run()

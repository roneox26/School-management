"""
Flask application entry point for Render deployment.
"""
import os
import sys

# Ensure current directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Flask app and initialization
from main import app, init_app

# Initialize database and create default admin
init_app()

# This is what gunicorn will call
if __name__ == "__main__":
    app.run()

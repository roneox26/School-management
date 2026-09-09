"""
WSGI entry point for Render deployment.
This file is used by gunicorn to run the application.
"""

import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and initialize the Flask app
from main import app, init_app

# Initialize the database and create default admin on startup
init_app()

if __name__ == "__main__":
    app.run()

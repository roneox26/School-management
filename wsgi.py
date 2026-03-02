"""
WSGI entry point for Render deployment.
This file is used by gunicorn to run the application.
"""

import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and initialize the Flask app
from main import app

# Initialize the database on startup
from main import init_app
init_app()

if __name__ == "__main__":
    app.run()

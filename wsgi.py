"""
WSGI entry point for Render deployment.
This file is used by gunicorn to run the application.
"""

import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# `main` initializes the application during import.
from main import app

if __name__ == "__main__":
    app.run()

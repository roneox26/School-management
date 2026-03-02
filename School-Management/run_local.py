
import os
import sys

# Ensure requirements are installed
try:
    import flask
    import flask_login
    import flask_mail
    import reportlab
except ImportError:
    print("Missing dependencies. Please run: pip install -r requirements.txt")
    sys.exit(1)

# Import the application
try:
    print("Starting School Management System...")
    import main
    
    # Initialize the database and seed data
    print("Initializing application data...")
    main.init_app()
    
    # Run the Flask app
    if __name__ == "__main__":
        print("Use http://127.0.0.1:5000 to access the application")
        main.app.run(host='127.0.0.1', port=5000, debug=True)

except Exception as e:
    print(f"Error starting application: {e}")
    import traceback
    traceback.print_exc()

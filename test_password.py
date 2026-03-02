import sys
sys.path.insert(0, 'School-Management')

from werkzeug.security import check_password_hash, generate_password_hash
from main import get_from_db, init_app

# Initialize app to create default admin
init_app()

print("=== ADMIN PASSWORD VERIFICATION TEST ===")

# Get admin from database
admins = get_from_db('admin')
if isinstance(admins, list) and len(admins) > 0:
    admin = admins[0]
    username = admin.get('username')
    stored_hash = admin.get('password_hash')
    
    print(f"Username from DB: {username}")
    print(f"Stored hash: {stored_hash[:40]}...")
    
    # Test with correct password
    test_password = 'password123'
    result = check_password_hash(stored_hash, test_password)
    print(f"\nPassword check for '{test_password}': {result}")
    
    # Test with wrong password
    wrong_password = 'wrongpassword'
    result2 = check_password_hash(stored_hash, wrong_password)
    print(f"Password check for '{wrong_password}': {result2}")
else:
    print("No admins found in database!")

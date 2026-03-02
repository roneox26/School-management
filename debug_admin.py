import sys
sys.path.insert(0, 'School-Management')

from main import get_from_db, check_password_hash, generate_password_hash

# Check existing admins
admins = get_from_db('admin')
print("=== EXISTING ADMINS ===")
if isinstance(admins, list):
    print(f"Found {len(admins)} admin(s):")
    for admin in admins:
        print(f"  Username: {admin.get('username')}")
        print(f"  Hash: {admin.get('password_hash')[:30]}...")
else:
    print("No admins found")

# Test password hashing
print("\n=== PASSWORD TEST ===")
test_password = 'password123'
test_hash = generate_password_hash(test_password)
print(f"Test password: {test_password}")
print(f"Test hash: {test_hash[:30]}...")
print(f"Hash verification: {check_password_hash(test_hash, test_password)}")

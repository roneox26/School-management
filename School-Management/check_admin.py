import sqlite3
import json

conn = sqlite3.connect('school_management.db')
rows = conn.execute('SELECT data FROM app_data WHERE collection="admin"').fetchall()

print("\n" + "=" * 60)
print("CURRENT ADMIN USERS IN DATABASE")
print("=" * 60)
print(f"\nTotal admin users: {len(rows)}\n")

for idx, row in enumerate(rows, 1):
    admin = json.loads(row[0])
    print(f"{idx}. Username: {admin['username']}")
    print(f"   Email: {admin['email']}")
    print(f"   ID: {admin['id'][:8]}...")
    print()

print("=" * 60)
conn.close()

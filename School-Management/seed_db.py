
import json
import uuid
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash

def create_admin(username, password):
    return {
        "id": str(uuid.uuid4()),
        "username": username,
        "email": f"{username}@example.com",
        "password_hash": generate_password_hash(password),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

data = {}

# User '7' with password 'pass'
user1 = create_admin("7", "pass")
data[f"admin:{user1['id']}"] = user1

# User '7' with password '7' (just in case)
# Cannot have duplicate usernames usually, but our simple DB query might allow it or find the first one.
# query_db filters by value.
# I'll stick with 7/pass first.

# Default admin
user_admin = create_admin("admin", "admin")
data[f"admin:{user_admin['id']}"] = user_admin

with open("local_db.json", "w") as f:
    json.dump(data, f, indent=2)

print("Database seeded locally.")

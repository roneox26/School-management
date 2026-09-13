#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Deploy-time Admin Creation Script
Automatically creates admin user from environment variables.
Run this script during deployment (build or release phase).
"""

import os
import json
import uuid
import sys
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash

# ── Read credentials from environment variables ──────────────────────────────
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "Rone16")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Rone@##16")
ADMIN_EMAIL    = os.environ.get("ADMIN_EMAIL",    "roneox16@gmail.com")
DATABASE_URL   = os.environ.get("DATABASE_URL")

def get_connection():
    """Return a DB connection — PostgreSQL or SQLite."""
    if DATABASE_URL and DATABASE_URL.startswith("postgresql"):
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        return conn, "postgres"
    else:
        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "school_management.db")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn, "sqlite"


def ensure_table(conn, db_type):
    """Create app_data table if it does not exist."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_data (
            collection TEXT,
            id         TEXT,
            data       TEXT,
            PRIMARY KEY (collection, id)
        )
    """)
    conn.commit()
    print("[DEPLOY] app_data table ready.")


def create_or_update_admin(conn, db_type):
    """Insert or update the admin user."""
    cursor = conn.cursor()

    # Check if admin with this username already exists
    if db_type == "postgres":
        cursor.execute(
            "SELECT id, data FROM app_data WHERE collection = %s",
            ("admin",)
        )
    else:
        cursor.execute(
            "SELECT id, data FROM app_data WHERE collection = ?",
            ("admin",)
        )

    rows = cursor.fetchall()
    existing_id = None

    for row in rows:
        row_data = json.loads(row[1] if db_type == "postgres" else row["data"])
        if row_data.get("username") == ADMIN_USERNAME:
            existing_id = row[0] if db_type == "postgres" else row["id"]
            break

    password_hash = generate_password_hash(ADMIN_PASSWORD)
    now = datetime.now(timezone.utc).isoformat()

    if existing_id:
        # Update existing admin password
        admin_data = json.loads(row_data if isinstance(row_data, str) else json.dumps(row_data))
        admin_data["password_hash"] = password_hash
        admin_data["email"]         = ADMIN_EMAIL
        admin_data["updated_at"]    = now

        if db_type == "postgres":
            cursor.execute(
                "UPDATE app_data SET data = %s WHERE collection = %s AND id = %s",
                (json.dumps(admin_data), "admin", existing_id)
            )
        else:
            cursor.execute(
                "UPDATE app_data SET data = ? WHERE collection = ? AND id = ?",
                (json.dumps(admin_data), "admin", existing_id)
            )

        conn.commit()
        print(f"[DEPLOY] ✅ Admin updated  → username: {ADMIN_USERNAME}")

    else:
        # Create new admin
        admin_id   = str(uuid.uuid4())
        admin_data = {
            "id":            admin_id,
            "username":      ADMIN_USERNAME,
            "email":         ADMIN_EMAIL,
            "password_hash": password_hash,
            "is_active":     True,
            "created_at":    now,
        }

        if db_type == "postgres":
            cursor.execute(
                "INSERT INTO app_data (collection, id, data) VALUES (%s, %s, %s)",
                ("admin", admin_id, json.dumps(admin_data))
            )
        else:
            cursor.execute(
                "INSERT INTO app_data (collection, id, data) VALUES (?, ?, ?)",
                ("admin", admin_id, json.dumps(admin_data))
            )

        conn.commit()
        print(f"[DEPLOY] ✅ Admin created  → username: {ADMIN_USERNAME}")

    print(f"[DEPLOY]    email   : {ADMIN_EMAIL}")
    print(f"[DEPLOY]    db type : {db_type}")


def main():
    print("[DEPLOY] ══════════════════════════════════════")
    print("[DEPLOY]  Admin Setup — School Management")
    print("[DEPLOY] ══════════════════════════════════════")

    try:
        conn, db_type = get_connection()
        ensure_table(conn, db_type)
        create_or_update_admin(conn, db_type)
        conn.close()
        print("[DEPLOY] ══════════════════════════════════════")
        print("[DEPLOY] Done! You can now log in.")
        print("[DEPLOY] ══════════════════════════════════════")
    except Exception as e:
        print(f"[DEPLOY] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

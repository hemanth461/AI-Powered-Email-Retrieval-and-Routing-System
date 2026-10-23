"""
One-off script to create all PostgreSQL tables.
Run once after setting DATABASE_URL in .env and creating the database itself:

    createdb email_triage      # or via psql: CREATE DATABASE email_triage;
    python scripts/init_db.py
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.db import init_db

if __name__ == "__main__":
    init_db()
    print("[OK] Database tables created (or already existed).")

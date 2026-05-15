"""Database migration / initialisation script.

Creates all tables (idempotent — safe to run multiple times).
Swap DATABASE_URL env var to a PostgreSQL connection string for production.

Usage:
    python -m migrations.init_db
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.db.models import Base, engine


def run_migrations():
    print("Running migrations…")
    Base.metadata.create_all(bind=engine)
    print("Tables created (if not already present):")
    for table in Base.metadata.sorted_tables:
        print(f"  [ok] {table.name}")
    print("Migration complete.")


if __name__ == "__main__":
    run_migrations()

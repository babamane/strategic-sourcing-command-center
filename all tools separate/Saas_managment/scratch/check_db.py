import sqlite3
import os
from datetime import datetime

DB_PATH = "data/saas_spend.db"

def check():
    if not os.path.exists(DB_PATH):
        print(f"DB not found at {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Integrity check
        print("Running integrity check...")
        res = conn.execute("PRAGMA integrity_check;").fetchone()
        print(f"Integrity result: {res[0]}")

        # Check data_versions
        print("\nLast 5 data_versions:")
        rows = conn.execute("SELECT * FROM data_versions ORDER BY version_id DESC LIMIT 5").fetchall()
        for r in rows:
            print(r)

        # Check current_versions
        print("\nCurrent versions:")
        rows = conn.execute("SELECT * FROM current_versions").fetchall()
        for r in rows:
            print(r)

        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check()

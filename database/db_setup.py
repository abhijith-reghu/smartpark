"""
Creates the SmartPark SQLite database and applies the schema.
Run this once to initialize database/smartpark.db
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "smartpark.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def create_database():
    conn = sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH, "r") as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)
    conn.commit()
    conn.close()
    print(f"Database created at {DB_PATH}")


if __name__ == "__main__":
    create_database()
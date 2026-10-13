"""
Populates the database with initial sections, 25 parking slots (5 sections, A-E),
and one staff account for login testing.
Run this after db_setup.py, once.
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), "smartpark.db")


def seed():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Sections: (name, direction)
    sections = [
        ("A", "LEFT1"),
        ("B", "LEFT2"),
        ("C", "STRAIGHT"),
        ("D", "RIGHT1"),
        ("E", "RIGHT2"),
    ]
    for name, direction in sections:
        cur.execute(
            "INSERT OR IGNORE INTO sections (name, direction) VALUES (?, ?)",
            (name, direction),
        )
    conn.commit()

    # Slots: 5 per section -> A1-A5, B1-B5, ... E1-E5 (distance 1 to 5)
    slots = []
    for name, _ in sections:
        cur.execute("SELECT section_id FROM sections WHERE name = ?", (name,))
        section_id = cur.fetchone()[0]
        for n in range(1, 6):
            slots.append((f"{name}{n}", section_id, n))

    for slot_code, section_id, distance in slots:
        cur.execute(
            """INSERT OR IGNORE INTO parking_slots
               (slot_code, section_id, status, distance_from_entrance)
               VALUES (?, ?, 'available', ?)""",
            (slot_code, section_id, distance),
        )

    # Staff account for testing login (username: admin, password: admin123)
    password_hash = generate_password_hash("admin123")
    cur.execute(
        """INSERT OR IGNORE INTO staff (username, password_hash, full_name)
           VALUES (?, ?, ?)""",
        ("admin", password_hash, "Test Admin"),
    )

    conn.commit()
    conn.close()
    print("Seed data inserted: 5 sections, 25 slots, 1 staff account (admin/admin123).")


if __name__ == "__main__":
    seed()
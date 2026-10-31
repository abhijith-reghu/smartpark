
import sqlite3
from pathlib import Path
from config import DB_PATH
from werkzeug.security import generate_password_hash

BASE_DIR = Path(__file__).resolve().parent.parent
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())

    sections = [
        ("A", "LEFT1"),
        ("B", "LEFT2"),
        ("C", "STRAIGHT"),
        ("D", "RIGHT1"),
        ("E", "RIGHT2"),
    ]

    for name, direction in sections:
        conn.execute(
            "INSERT OR IGNORE INTO sections (name, direction) VALUES (?, ?)",
            (name, direction)
        )

        section_id = conn.execute(
            "SELECT section_id FROM sections WHERE name = ?",
            (name,)
        ).fetchone()[0]

        for n in range(1, 6):
            conn.execute(
                """INSERT OR IGNORE INTO parking_slots
                (slot_code, section_id, status, distance_from_entrance)
                VALUES (?, ?, 'available', ?)""",
                (f"{name}{n}", section_id, n)
            )

    conn.execute(
        """INSERT OR IGNORE INTO staff
        (username, password_hash, full_name)
        VALUES (?, ?, ?)""",
        ("admin", generate_password_hash("admin123"), "Test Admin")
    )

    conn.commit()
    conn.close()

-- SmartPark Database Schema (v2 - Staff/Admin Module)

CREATE TABLE IF NOT EXISTS sections (
    section_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    direction TEXT NOT NULL CHECK(direction IN ('LEFT1', 'LEFT2', 'STRAIGHT', 'RIGHT1', 'RIGHT2'))
);

CREATE TABLE IF NOT EXISTS parking_slots (
    slot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_code TEXT NOT NULL UNIQUE,
    section_id INTEGER NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('available', 'occupied')) DEFAULT 'available',
    distance_from_entrance INTEGER NOT NULL,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (section_id) REFERENCES sections(section_id)
);

CREATE TABLE IF NOT EXISTS staff (
    staff_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS parking_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_id INTEGER NOT NULL,
    event_type TEXT NOT NULL CHECK(event_type IN ('occupied', 'vacated')),
    changed_by INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (slot_id) REFERENCES parking_slots(slot_id),
    FOREIGN KEY (changed_by) REFERENCES staff(staff_id)
);
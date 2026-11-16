"""
database.py - SQLite Database Management Module
Smart Medication Reminder & Health Tracker

This module initializes the SQLite database, manages table schemas,
enforces relational integrity, and provides sample demonstration data.
"""

import os
import sqlite3
from datetime import datetime, date, timedelta

# Database file location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "medication.db")


def get_connection():
    """
    Establish and return a SQLite database connection.
    Enforces foreign key constraints and provides row dict-like access.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Create necessary database tables if they do not exist.
    Tables:
    1. MEDICINES - Stores medicine details, dosage, frequency, and schedules.
    2. DOSE_HISTORY - Tracks medication intake status (Pending, Taken, Missed, Skipped).
    3. HEALTH_RECORDS - Tracks health vitals (Weight, BP, Heart Rate).
    """
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Medicines Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            dosage TEXT NOT NULL,
            frequency TEXT NOT NULL,
            scheduled_time TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            instructions TEXT
        );
    """)

    # 2. Dose History Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dose_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medicine_id INTEGER NOT NULL,
            scheduled_datetime TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('Pending', 'Taken', 'Missed', 'Skipped')),
            taken_at TEXT,
            FOREIGN KEY (medicine_id) REFERENCES medicines (id) ON DELETE CASCADE,
            UNIQUE(medicine_id, scheduled_datetime)
        );
    """)

    # 3. Health Records Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS health_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            weight REAL NOT NULL,
            systolic_bp INTEGER NOT NULL,
            diastolic_bp INTEGER NOT NULL,
            heart_rate INTEGER NOT NULL,
            notes TEXT
        );
    """)

    conn.commit()
    conn.close()


def load_sample_data():
    """
    Load realistic demonstration data for college project presentation.
    Includes:
    - 4 Sample Medicines with different timings and frequencies
    - Past & Today Dose History (Taken, Missed, Skipped, Pending)
    - 7 Daily Health Records
    Never overwrites existing records if sample data already exists.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Check if medicines already exist to avoid duplicate demo insertion
    cursor.execute("SELECT COUNT(*) AS count FROM medicines WHERE instructions LIKE '%[Demo Data]%'")
    if cursor.fetchone()["count"] > 0:
        conn.close()
        return False, "Demo data is already loaded in the database."

    today = date.today()
    yesterday = today - timedelta(days=1)
    two_days_ago = today - timedelta(days=2)
    start_demo = today - timedelta(days=7)
    end_demo = today + timedelta(days=30)

    # 1. Insert 4 Sample Medicines
    sample_medicines = [
        (
            "Amoxicillin",
            "500 mg",
            "Twice daily",
            "08:00, 20:00",
            start_demo.strftime("%Y-%m-%d"),
            end_demo.strftime("%Y-%m-%d"),
            "Take with a full glass of water after meals. [Demo Data]"
        ),
        (
            "Metformin",
            "850 mg",
            "Once daily",
            "09:00",
            start_demo.strftime("%Y-%m-%d"),
            end_demo.strftime("%Y-%m-%d"),
            "Take with breakfast to minimize stomach upset. [Demo Data]"
        ),
        (
            "Atorvastatin",
            "20 mg",
            "Once daily",
            "21:00",
            start_demo.strftime("%Y-%m-%d"),
            end_demo.strftime("%Y-%m-%d"),
            "Take at bedtime for cholesterol management. [Demo Data]"
        ),
        (
            "Vitamin D3",
            "1000 IU",
            "Once daily",
            "10:00",
            start_demo.strftime("%Y-%m-%d"),
            end_demo.strftime("%Y-%m-%d"),
            "Take after morning meal. [Demo Data]"
        )
    ]

    med_ids = []
    for med in sample_medicines:
        cursor.execute("""
            INSERT INTO medicines (name, dosage, frequency, scheduled_time, start_date, end_date, instructions)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, med)
        med_ids.append(cursor.lastrowid)

    amox_id, met_id, ator_id, vit_id = med_ids

    # 2. Insert Sample Doses across recent days (Taken, Missed, Skipped, Pending)
    # Two days ago
    cursor.execute("""
        INSERT OR IGNORE INTO dose_history (medicine_id, scheduled_datetime, status, taken_at)
        VALUES (?, ?, 'Taken', ?)
    """, (amox_id, f"{two_days_ago} 08:00", f"{two_days_ago} 08:15:00"))

    cursor.execute("""
        INSERT OR IGNORE INTO dose_history (medicine_id, scheduled_datetime, status, taken_at)
        VALUES (?, ?, 'Taken', ?)
    """, (met_id, f"{two_days_ago} 09:00", f"{two_days_ago} 09:05:00"))

    cursor.execute("""
        INSERT OR IGNORE INTO dose_history (medicine_id, scheduled_datetime, status, taken_at)
        VALUES (?, ?, 'Taken', ?)
    """, (vit_id, f"{two_days_ago} 10:00", f"{two_days_ago} 10:10:00"))

    cursor.execute("""
        INSERT OR IGNORE INTO dose_history (medicine_id, scheduled_datetime, status, taken_at)
        VALUES (?, ?, 'Taken', ?)
    """, (amox_id, f"{two_days_ago} 20:00", f"{two_days_ago} 20:05:00"))

    cursor.execute("""
        INSERT OR IGNORE INTO dose_history (medicine_id, scheduled_datetime, status, taken_at)
        VALUES (?, ?, 'Taken', ?)
    """, (ator_id, f"{two_days_ago} 21:00", f"{two_days_ago} 21:12:00"))

    # Yesterday: Amoxicillin morning Taken, Metformin Taken, Vitamin D3 Missed, Amoxicillin evening Skipped, Atorvastatin Taken
    cursor.execute("""
        INSERT OR IGNORE INTO dose_history (medicine_id, scheduled_datetime, status, taken_at)
        VALUES (?, ?, 'Taken', ?)
    """, (amox_id, f"{yesterday} 08:00", f"{yesterday} 08:20:00"))

    cursor.execute("""
        INSERT OR IGNORE INTO dose_history (medicine_id, scheduled_datetime, status, taken_at)
        VALUES (?, ?, 'Taken', ?)
    """, (met_id, f"{yesterday} 09:00", f"{yesterday} 09:10:00"))

    cursor.execute("""
        INSERT OR IGNORE INTO dose_history (medicine_id, scheduled_datetime, status, taken_at)
        VALUES (?, ?, 'Missed', NULL)
    """, (vit_id, f"{yesterday} 10:00"))

    cursor.execute("""
        INSERT OR IGNORE INTO dose_history (medicine_id, scheduled_datetime, status, taken_at)
        VALUES (?, ?, 'Skipped', NULL)
    """, (amox_id, f"{yesterday} 20:00"))

    cursor.execute("""
        INSERT OR IGNORE INTO dose_history (medicine_id, scheduled_datetime, status, taken_at)
        VALUES (?, ?, 'Taken', ?)
    """, (ator_id, f"{yesterday} 21:00", f"{yesterday} 21:05:00"))

    # Today doses
    now_time = datetime.now().strftime("%H:%M")
    today_str = today.strftime("%Y-%m-%d")

    # Morning dose today marked Taken
    cursor.execute("""
        INSERT OR IGNORE INTO dose_history (medicine_id, scheduled_datetime, status, taken_at)
        VALUES (?, ?, 'Taken', ?)
    """, (amox_id, f"{today_str} 08:00", f"{today_str} 08:08:00"))

    # Metformin today Pending
    cursor.execute("""
        INSERT OR IGNORE INTO dose_history (medicine_id, scheduled_datetime, status, taken_at)
        VALUES (?, ?, 'Pending', NULL)
    """, (met_id, f"{today_str} 09:00"))

    # Vitamin D3 today Pending
    cursor.execute("""
        INSERT OR IGNORE INTO dose_history (medicine_id, scheduled_datetime, status, taken_at)
        VALUES (?, ?, 'Pending', NULL)
    """, (vit_id, f"{today_str} 10:00"))

    # 3. Insert 7 Sample Health Records (Daily for the past 7 days)
    sample_health = [
        (today - timedelta(days=6), 72.5, 124, 82, 74, "Initial checkup reading [Demo Data]"),
        (today - timedelta(days=5), 72.3, 122, 80, 72, "Morning reading before breakfast [Demo Data]"),
        (today - timedelta(days=4), 72.0, 120, 80, 70, "Routine post-walk checkup [Demo Data]"),
        (today - timedelta(days=3), 71.8, 118, 78, 68, "Felt energetic and rested [Demo Data]"),
        (today - timedelta(days=2), 71.9, 121, 79, 71, "Evening measurement [Demo Data]"),
        (today - timedelta(days=1), 71.6, 119, 78, 69, "Normal baseline blood pressure [Demo Data]"),
        (today, 71.5, 118, 76, 70, "Today's morning vitals [Demo Data]")
    ]

    for h_date, weight, sys_bp, dia_bp, hr, notes in sample_health:
        cursor.execute("""
            INSERT INTO health_records (date, weight, systolic_bp, diastolic_bp, heart_rate, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (h_date.strftime("%Y-%m-%d"), weight, sys_bp, dia_bp, hr, notes))

    conn.commit()
    conn.close()
    return True, "Sample demonstration data loaded successfully!"


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", DB_PATH)

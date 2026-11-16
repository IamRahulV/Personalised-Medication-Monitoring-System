"""
medication.py - Medication CRUD Operations Module
Smart Medication Reminder & Health Tracker

This module handles the business logic and database queries for:
- Adding new medicines
- Retrieving medicine records
- Updating existing medicines
- Deleting medicines
- Searching medicines
- Comprehensive input validation
"""

import re
from datetime import datetime, date
import pandas as pd
from database import get_connection


def validate_time_format(time_str: str) -> bool:
    """
    Validate that a scheduled time string matches 'HH:MM' or
    multiple times separated by comma (e.g. '08:00, 20:00').
    """
    if not time_str or not time_str.strip():
        return False
    parts = [t.strip() for t in time_str.split(",")]
    time_regex = r"^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$"
    for part in parts:
        if not re.match(time_regex, part):
            return False
    return True


def validate_medicine_data(name, dosage, frequency, scheduled_time, start_date, end_date):
    """
    Validates input fields for creating or updating a medicine.
    Returns (is_valid: bool, error_message: str).
    """
    if not name or not name.strip():
        return False, "Medicine name cannot be empty."

    if not dosage or not dosage.strip():
        return False, "Dosage cannot be empty (e.g., '500 mg', '1 tablet')."

    if not frequency or not frequency.strip():
        return False, "Please select a valid frequency."

    if not validate_time_format(scheduled_time):
        return False, "Scheduled time must be in 24-hour HH:MM format (e.g., '08:00' or '08:00, 20:00')."

    # Validate dates
    try:
        if isinstance(start_date, str):
            s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        else:
            s_date = start_date

        if isinstance(end_date, str):
            e_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        else:
            e_date = end_date

        if e_date < s_date:
            return False, "End date cannot be earlier than start date."
    except Exception as e:
        return False, f"Invalid date format: {str(e)}"

    return True, ""


def add_medicine(name, dosage, frequency, scheduled_time, start_date, end_date, instructions=""):
    """
    Add a new medicine record to the database.
    """
    is_valid, err = validate_medicine_data(name, dosage, frequency, scheduled_time, start_date, end_date)
    if not is_valid:
        return False, err, None

    # Format dates
    s_date_str = start_date.strftime("%Y-%m-%d") if hasattr(start_date, "strftime") else str(start_date)
    e_date_str = end_date.strftime("%Y-%m-%d") if hasattr(end_date, "strftime") else str(end_date)
    clean_time = ", ".join([t.strip() for t in scheduled_time.split(",")])

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO medicines (name, dosage, frequency, scheduled_time, start_date, end_date, instructions)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name.strip(), dosage.strip(), frequency.strip(), clean_time, s_date_str, e_date_str, instructions.strip()))
        conn.commit()
        med_id = cursor.lastrowid
        return True, f"Medicine '{name.strip()}' added successfully!", med_id
    except Exception as e:
        conn.rollback()
        return False, f"Database error: {str(e)}", None
    finally:
        conn.close()


def get_all_medicines() -> pd.DataFrame:
    """
    Retrieve all medicines as a Pandas DataFrame.
    """
    conn = get_connection()
    try:
        query = "SELECT * FROM medicines ORDER BY name ASC"
        df = pd.read_sql_query(query, conn)
        return df
    finally:
        conn.close()


def get_active_medicines(reference_date=None) -> pd.DataFrame:
    """
    Retrieve medicines active on the given reference_date (defaults to today).
    """
    if reference_date is None:
        ref_str = date.today().strftime("%Y-%m-%d")
    elif hasattr(reference_date, "strftime"):
        ref_str = reference_date.strftime("%Y-%m-%d")
    else:
        ref_str = str(reference_date)

    conn = get_connection()
    try:
        query = """
            SELECT * FROM medicines 
            WHERE start_date <= ? AND end_date >= ?
            ORDER BY scheduled_time ASC
        """
        df = pd.read_sql_query(query, conn, params=(ref_str, ref_str))
        return df
    finally:
        conn.close()


def get_medicine_by_id(med_id: int):
    """
    Retrieve single medicine details by primary key ID.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM medicines WHERE id = ?", (med_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        conn.close()


def update_medicine(med_id: int, name, dosage, frequency, scheduled_time, start_date, end_date, instructions=""):
    """
    Update an existing medicine record.
    """
    is_valid, err = validate_medicine_data(name, dosage, frequency, scheduled_time, start_date, end_date)
    if not is_valid:
        return False, err

    s_date_str = start_date.strftime("%Y-%m-%d") if hasattr(start_date, "strftime") else str(start_date)
    e_date_str = end_date.strftime("%Y-%m-%d") if hasattr(end_date, "strftime") else str(end_date)
    clean_time = ", ".join([t.strip() for t in scheduled_time.split(",")])

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE medicines 
            SET name = ?, dosage = ?, frequency = ?, scheduled_time = ?, 
                start_date = ?, end_date = ?, instructions = ?
            WHERE id = ?
        """, (name.strip(), dosage.strip(), frequency.strip(), clean_time, s_date_str, e_date_str, instructions.strip(), med_id))
        conn.commit()
        if cursor.rowcount > 0:
            return True, f"Medicine '{name.strip()}' updated successfully!"
        return False, "Medicine not found or no changes made."
    except Exception as e:
        conn.rollback()
        return False, f"Database error: {str(e)}"
    finally:
        conn.close()


def delete_medicine(med_id: int):
    """
    Delete a medicine and its associated dose history records (via CASCADE).
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM medicines WHERE id = ?", (med_id,))
        conn.commit()
        if cursor.rowcount > 0:
            return True, "Medicine deleted successfully!"
        return False, "Medicine not found."
    except Exception as e:
        conn.rollback()
        return False, f"Database error: {str(e)}"
    finally:
        conn.close()


def search_medicines(keyword: str) -> pd.DataFrame:
    """
    Search medicines by name, dosage, or instructions.
    """
    if not keyword or not keyword.strip():
        return get_all_medicines()

    conn = get_connection()
    try:
        term = f"%{keyword.strip()}%"
        query = """
            SELECT * FROM medicines 
            WHERE name LIKE ? OR dosage LIKE ? OR instructions LIKE ? OR frequency LIKE ?
            ORDER BY name ASC
        """
        df = pd.read_sql_query(query, conn, params=(term, term, term, term))
        return df
    finally:
        conn.close()

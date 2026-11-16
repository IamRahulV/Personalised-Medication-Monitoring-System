"""
health.py - Health Vitals Tracking Module
Smart Medication Reminder & Health Tracker

This module manages:
- Logging daily health measurements (Weight, Blood Pressure, Heart Rate)
- Validation of vital measurements
- Retrieving historical health data
- Deleting health records
- Evaluating Blood Pressure classifications according to clinical standards
"""

from datetime import datetime, date
import pandas as pd
from database import get_connection


def classify_blood_pressure(systolic: int, diastolic: int) -> dict:
    """
    Classify blood pressure reading based on standard clinical guidelines (AHA/WHO).
    Returns a dictionary with status, category, and recommended display color.
    """
    if systolic > 180 or diastolic > 120:
        return {
            "category": "Hypertensive Crisis",
            "status": "danger",
            "badge_color": "#D32F2F",
            "advice": "Emergency: Consult a doctor immediately."
        }
    elif systolic >= 140 or diastolic >= 90:
        return {
            "category": "Stage 2 Hypertension",
            "status": "warning",
            "badge_color": "#F57C00",
            "advice": "High blood pressure: Monitor regularly and consult healthcare provider."
        }
    elif (130 <= systolic <= 139) or (80 <= diastolic <= 89):
        return {
            "category": "Stage 1 Hypertension",
            "status": "attention",
            "badge_color": "#FFA000",
            "advice": "Pre-hypertension: Maintain healthy lifestyle and low sodium diet."
        }
    elif 120 <= systolic <= 129 and diastolic < 80:
        return {
            "category": "Elevated",
            "status": "caution",
            "badge_color": "#1976D2",
            "advice": "Slightly elevated: Adopt active habits."
        }
    elif systolic < 120 and diastolic < 80:
        return {
            "category": "Normal",
            "status": "healthy",
            "badge_color": "#388E3C",
            "advice": "Healthy blood pressure range."
        }
    else:
        return {
            "category": "Unclassified",
            "status": "info",
            "badge_color": "#0288D1",
            "advice": "Normal range variation."
        }


def validate_health_inputs(rec_date, weight, systolic, diastolic, heart_rate):
    """
    Validate health record measurements:
    - Weight: > 0 and reasonable (< 500 kg)
    - Systolic & Diastolic: positive integers, Systolic > Diastolic
    - Heart rate: positive integer between 30 and 250 BPM
    Returns (is_valid: bool, error_message: str).
    """
    # 1. Date check
    try:
        if isinstance(rec_date, str):
            datetime.strptime(rec_date, "%Y-%m-%d")
    except Exception:
        return False, "Invalid date format. Use YYYY-MM-DD."

    # 2. Weight check
    try:
        wt = float(weight)
        if wt <= 0 or wt > 500:
            return False, "Weight must be a positive number between 1 and 500 kg."
    except (ValueError, TypeError):
        return False, "Weight must be a valid numeric value."

    # 3. Blood Pressure check
    try:
        sys_bp = int(systolic)
        dia_bp = int(diastolic)
        if sys_bp <= 40 or sys_bp >= 300:
            return False, "Systolic BP must be between 40 and 300 mmHg."
        if dia_bp <= 30 or dia_bp >= 200:
            return False, "Diastolic BP must be between 30 and 200 mmHg."
        if dia_bp >= sys_bp:
            return False, "Systolic pressure must be strictly greater than Diastolic pressure."
    except (ValueError, TypeError):
        return False, "Blood pressure values must be valid whole numbers."

    # 4. Heart Rate check
    try:
        hr = int(heart_rate)
        if hr < 30 or hr > 250:
            return False, "Heart rate must be between 30 and 250 BPM."
    except (ValueError, TypeError):
        return False, "Heart rate must be a valid integer."

    return True, ""


def add_health_record(rec_date, weight, systolic, diastolic, heart_rate, notes=""):
    """
    Insert a new health vital record into SQLite.
    """
    is_valid, err = validate_health_inputs(rec_date, weight, systolic, diastolic, heart_rate)
    if not is_valid:
        return False, err

    date_str = rec_date.strftime("%Y-%m-%d") if hasattr(rec_date, "strftime") else str(rec_date)

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO health_records (date, weight, systolic_bp, diastolic_bp, heart_rate, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (date_str, float(weight), int(systolic), int(diastolic), int(heart_rate), notes.strip()))
        conn.commit()
        return True, "Health measurement logged successfully!"
    except Exception as e:
        conn.rollback()
        return False, f"Database error: {str(e)}"
    finally:
        conn.close()


def get_all_health_records(order_by="DESC") -> pd.DataFrame:
    """
    Retrieve all health records.
    order_by: 'DESC' for viewing tables (newest first), 'ASC' for charts.
    """
    conn = get_connection()
    try:
        order = "DESC" if order_by.upper() == "DESC" else "ASC"
        query = f"SELECT * FROM health_records ORDER BY date {order}, id {order}"
        df = pd.read_sql_query(query, conn)
        return df
    finally:
        conn.close()


def get_recent_health_records(limit: int = 5) -> pd.DataFrame:
    """
    Retrieve the most recent health records for Dashboard display.
    """
    conn = get_connection()
    try:
        query = "SELECT * FROM health_records ORDER BY date DESC, id DESC LIMIT ?"
        df = pd.read_sql_query(query, conn, params=(limit,))
        return df
    finally:
        conn.close()


def delete_health_record(record_id: int):
    """
    Delete a health measurement record by ID.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM health_records WHERE id = ?", (record_id,))
        conn.commit()
        if cursor.rowcount > 0:
            return True, "Health record deleted successfully!"
        return False, "Health record not found."
    except Exception as e:
        conn.rollback()
        return False, f"Database error: {str(e)}"
    finally:
        conn.close()

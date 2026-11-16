"""
reminders.py - Medication Reminder Engine
Smart Medication Reminder & Health Tracker

This module handles:
- Detecting medicines that are due based on current date & time
- Creating 'Pending' dose records in SQLite without duplication
- Transitioning 'Pending' doses to 'Missed' after a configurable grace period
- Recording doses as 'Taken', 'Skipped', or 'Missed'
- Retrieving active reminders and today's schedule
"""

from datetime import datetime, date, timedelta
import pandas as pd
from database import get_connection


def check_and_sync_doses(grace_period_minutes: int = 60):
    """
    Core reminder engine function:
    1. Checks current date & time.
    2. Identifies all active medicines.
    3. For all doses scheduled up to now (today and up to past 3 days):
       - Inserts a 'Pending' dose record if within the grace period.
       - Inserts a 'Missed' dose record if the grace period has expired.
       - Prevents duplicate records using SQLite UNIQUE constraint & existence check.
    4. Auto-transitions older 'Pending' doses to 'Missed' once grace period expires.
    """
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now()
    today = now.date()

    # Look back up to 3 days to catch unrecorded doses if app was closed
    check_dates = [today - timedelta(days=d) for d in range(3, -1, -1)]

    try:
        # Step A: Update existing 'Pending' doses whose grace period has expired to 'Missed'
        cursor.execute("SELECT id, scheduled_datetime FROM dose_history WHERE status = 'Pending'")
        pending_doses = cursor.fetchall()
        for dose in pending_doses:
            dose_id = dose["id"]
            sched_dt_str = dose["scheduled_datetime"]
            try:
                sched_dt = datetime.strptime(sched_dt_str, "%Y-%m-%d %H:%M")
                elapsed_minutes = (now - sched_dt).total_seconds() / 60
                if elapsed_minutes > grace_period_minutes:
                    cursor.execute("UPDATE dose_history SET status = 'Missed' WHERE id = ?", (dose_id,))
            except Exception:
                continue

        # Step B: Check active medicines and generate doses for scheduled times that have arrived
        for day in check_dates:
            day_str = day.strftime("%Y-%m-%d")
            cursor.execute("""
                SELECT id, name, scheduled_time, start_date, end_date 
                FROM medicines
                WHERE start_date <= ? AND end_date >= ?
            """, (day_str, day_str))
            active_meds = cursor.fetchall()

            for med in active_meds:
                med_id = med["id"]
                times_str = med["scheduled_time"]
                # Parse multiple scheduled times if comma-separated
                time_list = [t.strip() for t in times_str.split(",") if t.strip()]

                for t_str in time_list:
                    scheduled_dt_str = f"{day_str} {t_str}"
                    try:
                        sched_dt = datetime.strptime(scheduled_dt_str, "%Y-%m-%d %H:%M")
                    except Exception:
                        continue

                    # Only process doses whose scheduled time has arrived or passed
                    if sched_dt <= now:
                        # Check if record already exists
                        cursor.execute("""
                            SELECT id, status FROM dose_history 
                            WHERE medicine_id = ? AND scheduled_datetime = ?
                        """, (med_id, scheduled_dt_str))
                        existing = cursor.fetchone()

                        if not existing:
                            elapsed = (now - sched_dt).total_seconds() / 60
                            initial_status = "Missed" if elapsed > grace_period_minutes else "Pending"
                            cursor.execute("""
                                INSERT OR IGNORE INTO dose_history (medicine_id, scheduled_datetime, status, taken_at)
                                VALUES (?, ?, ?, NULL)
                            """, (med_id, scheduled_dt_str, initial_status))

        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error syncing doses: {e}")
    finally:
        conn.close()


def get_active_reminders():
    """
    Retrieve all doses currently waiting for user action (status = 'Pending').
    Returns a list of dicts with medicine details.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 
                d.id AS dose_id,
                d.medicine_id,
                m.name AS medicine_name,
                m.dosage,
                m.frequency,
                m.instructions,
                d.scheduled_datetime,
                d.status
            FROM dose_history d
            JOIN medicines m ON d.medicine_id = m.id
            WHERE d.status = 'Pending'
            ORDER BY d.scheduled_datetime ASC
        """)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def mark_dose_taken(dose_id: int):
    """
    Mark a dose as 'Taken' and record the current timestamp.
    """
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE dose_history 
            SET status = 'Taken', taken_at = ?
            WHERE id = ?
        """, (now_str, dose_id))
        conn.commit()
        return True, "Dose marked as Taken successfully!"
    except Exception as e:
        conn.rollback()
        return False, f"Database error: {str(e)}"
    finally:
        conn.close()


def mark_dose_skipped(dose_id: int):
    """
    Mark a dose as 'Skipped'.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE dose_history 
            SET status = 'Skipped'
            WHERE id = ?
        """, (dose_id,))
        conn.commit()
        return True, "Dose marked as Skipped."
    except Exception as e:
        conn.rollback()
        return False, f"Database error: {str(e)}"
    finally:
        conn.close()


def mark_dose_missed(dose_id: int):
    """
    Mark a dose as 'Missed'.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE dose_history 
            SET status = 'Missed'
            WHERE id = ?
        """, (dose_id,))
        conn.commit()
        return True, "Dose marked as Missed."
    except Exception as e:
        conn.rollback()
        return False, f"Database error: {str(e)}"
    finally:
        conn.close()


def get_today_schedule() -> pd.DataFrame:
    """
    Retrieve today's complete schedule including Taken, Pending, Missed,
    Skipped, and Upcoming (future doses today not yet due).
    """
    today_str = date.today().strftime("%Y-%m-%d")
    now = datetime.now()

    conn = get_connection()
    try:
        # 1. Doses already in dose_history for today
        query = """
            SELECT 
                d.id AS dose_id,
                m.id AS medicine_id,
                m.name AS medicine_name,
                m.dosage,
                d.scheduled_datetime,
                d.status,
                d.taken_at,
                m.instructions
            FROM dose_history d
            JOIN medicines m ON d.medicine_id = m.id
            WHERE d.scheduled_datetime LIKE ?
            ORDER BY d.scheduled_datetime ASC
        """
        df_recorded = pd.read_sql_query(query, conn, params=(f"{today_str}%",))

        # 2. Check for active medicines scheduled later today (Upcoming)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, dosage, scheduled_time, instructions 
            FROM medicines
            WHERE start_date <= ? AND end_date >= ?
        """, (today_str, today_str))
        active_meds = cursor.fetchall()

        upcoming_records = []
        recorded_sched_times = set(df_recorded["scheduled_datetime"].tolist()) if not df_recorded.empty else set()

        for med in active_meds:
            times = [t.strip() for t in med["scheduled_time"].split(",") if t.strip()]
            for t_str in times:
                sched_dt_str = f"{today_str} {t_str}"
                if sched_dt_str not in recorded_sched_times:
                    try:
                        sched_dt = datetime.strptime(sched_dt_str, "%Y-%m-%d %H:%M")
                        if sched_dt > now:
                            upcoming_records.append({
                                "dose_id": None,
                                "medicine_id": med["id"],
                                "medicine_name": med["name"],
                                "dosage": med["dosage"],
                                "scheduled_datetime": sched_dt_str,
                                "status": "Upcoming",
                                "taken_at": None,
                                "instructions": med["instructions"]
                            })
                    except Exception:
                        continue

        if upcoming_records:
            df_upcoming = pd.DataFrame(upcoming_records)
            df_all = pd.concat([df_recorded, df_upcoming], ignore_index=True)
            df_all.sort_values(by="scheduled_datetime", inplace=True)
            return df_all

        return df_recorded
    finally:
        conn.close()

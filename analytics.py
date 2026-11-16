"""
analytics.py - Health & Medication Analytics Module
Smart Medication Reminder & Health Tracker

This module handles:
- Medication adherence calculation using formula:
  Adherence % = (Total Doses Taken / Total Scheduled Doses) * 100
- Breakdown of Taken, Missed, Pending, and Skipped doses
- Safe division by zero handling and exclusion of future doses
- Daily dose trend processing using Pandas
- Medication-wise adherence analysis
- Historical vital trends preparation for Streamlit native charts
"""

from datetime import datetime, date
import pandas as pd
from database import get_connection


def get_adherence_summary():
    """
    Calculate overall medication adherence statistics.
    Formula:
        Adherence Percentage = (Total Doses Taken / Total Scheduled Doses) * 100
    Scheduled doses include Taken, Missed, Skipped, and past Pending.
    Future doses are strictly excluded.
    Returns a dictionary of counts and adherence percentage.
    """
    conn = get_connection()
    try:
        query = """
            SELECT status, COUNT(*) AS count
            FROM dose_history
            GROUP BY status
        """
        df = pd.read_sql_query(query, conn)

        counts = {
            "Taken": 0,
            "Missed": 0,
            "Pending": 0,
            "Skipped": 0
        }

        for _, row in df.iterrows():
            st = row["status"]
            if st in counts:
                counts[st] = int(row["count"])

        taken = counts["Taken"]
        missed = counts["Missed"]
        skipped = counts["Skipped"]
        pending = counts["Pending"]

        # Total relevant scheduled doses for adherence
        total_evaluable = taken + missed + skipped

        if total_evaluable > 0:
            adherence_rate = round((taken / total_evaluable) * 100, 1)
        else:
            adherence_rate = 0.0

        return {
            "taken": taken,
            "missed": missed,
            "pending": pending,
            "skipped": skipped,
            "total_scheduled": total_evaluable + pending,
            "adherence_rate": adherence_rate
        }
    finally:
        conn.close()


def get_detailed_history(med_name_filter=None, status_filter=None, limit=200) -> pd.DataFrame:
    """
    Retrieve medication history records with medicine details and filters.
    """
    conn = get_connection()
    try:
        query = """
            SELECT 
                d.id AS history_id,
                m.name AS medicine_name,
                m.dosage,
                d.scheduled_datetime,
                SUBSTR(d.scheduled_datetime, 1, 10) AS dose_date,
                SUBSTR(d.scheduled_datetime, 12, 5) AS dose_time,
                d.status,
                d.taken_at,
                m.instructions
            FROM dose_history d
            JOIN medicines m ON d.medicine_id = m.id
            WHERE 1=1
        """
        params = []
        if med_name_filter and med_name_filter != "All":
            query += " AND m.name = ?"
            params.append(med_name_filter)
        if status_filter and status_filter != "All":
            query += " AND d.status = ?"
            params.append(status_filter)

        query += " ORDER BY d.scheduled_datetime DESC LIMIT ?"
        params.append(limit)

        df = pd.read_sql_query(query, conn, params=params)
        return df
    finally:
        conn.close()


def get_daily_adherence_trends() -> pd.DataFrame:
    """
    Aggregate taken and missed doses by date for Streamlit bar/line charts.
    Returns a DataFrame with date index and columns: [Taken, Missed, Skipped].
    """
    conn = get_connection()
    try:
        query = """
            SELECT 
                SUBSTR(scheduled_datetime, 1, 10) AS dose_date,
                status,
                COUNT(*) AS count
            FROM dose_history
            GROUP BY dose_date, status
            ORDER BY dose_date ASC
        """
        df = pd.read_sql_query(query, conn)
        if df.empty:
            return pd.DataFrame()

        # Pivot table to get statuses as columns
        pivot_df = df.pivot(index="dose_date", columns="status", values="count").fillna(0)

        # Ensure all expected columns exist
        for col in ["Taken", "Missed", "Skipped", "Pending"]:
            if col not in pivot_df.columns:
                pivot_df[col] = 0

        # Sort columns and reset index
        pivot_df = pivot_df[["Taken", "Missed", "Skipped", "Pending"]]
        return pivot_df
    finally:
        conn.close()


def get_medicine_wise_adherence() -> pd.DataFrame:
    """
    Calculate adherence rate per individual medicine.
    Returns DataFrame: [Medicine, Total Doses, Taken, Missed, Adherence %].
    """
    conn = get_connection()
    try:
        query = """
            SELECT 
                m.name AS medicine_name,
                d.status,
                COUNT(*) AS count
            FROM dose_history d
            JOIN medicines m ON d.medicine_id = m.id
            GROUP BY m.name, d.status
        """
        df = pd.read_sql_query(query, conn)
        if df.empty:
            return pd.DataFrame(columns=["Medicine", "Total Doses", "Taken", "Missed", "Adherence %"])

        med_groups = {}
        for _, row in df.iterrows():
            m_name = row["medicine_name"]
            status = row["status"]
            cnt = int(row["count"])

            if m_name not in med_groups:
                med_groups[m_name] = {"Taken": 0, "Missed": 0, "Skipped": 0, "Pending": 0}
            med_groups[m_name][status] = cnt

        data = []
        for m_name, counts in med_groups.items():
            taken = counts.get("Taken", 0)
            missed = counts.get("Missed", 0)
            skipped = counts.get("Skipped", 0)
            pending = counts.get("Pending", 0)
            evaluable = taken + missed + skipped
            rate = round((taken / evaluable) * 100, 1) if evaluable > 0 else 0.0

            data.append({
                "Medicine": m_name,
                "Total Evaluated": evaluable,
                "Taken": taken,
                "Missed": missed,
                "Skipped": skipped,
                "Pending": pending,
                "Adherence %": rate
            })

        result_df = pd.DataFrame(data)
        if not result_df.empty:
            result_df.sort_values(by="Adherence %", ascending=False, inplace=True)
        return result_df
    finally:
        conn.close()


def get_health_vitals_trends() -> pd.DataFrame:
    """
    Retrieve clean time-series health measurements for Streamlit charts.
    """
    conn = get_connection()
    try:
        query = """
            SELECT date, weight, systolic_bp, diastolic_bp, heart_rate
            FROM health_records
            ORDER BY date ASC, id ASC
        """
        df = pd.read_sql_query(query, conn)
        return df
    finally:
        conn.close()

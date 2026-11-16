"""
app.py - Main Application Portal & Entry Point
Smart Medication Reminder & Health Tracker
B.Tech CSE Healthcare College Project
"""

from datetime import datetime, date
import streamlit as st
from database import init_db, load_sample_data
from reminders import check_and_sync_doses, get_active_reminders, get_today_schedule
from medication import get_active_medicines
from analytics import get_adherence_summary

# Configure main application window
st.set_page_config(
    page_title="Smart Medication Reminder & Health Tracker",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 1. Initialize SQLite Database Tables safely
init_db()

# 2. Synchronize active reminders and doses
check_and_sync_doses(grace_period_minutes=60)

# Custom Healthcare Styling
st.markdown("""
<style>
    .main {
        background-color: #F8FAFC;
    }
    .hero-banner {
        background: linear-gradient(135deg, #0D47A1 0%, #1976D2 50%, #00897B 100%);
        padding: 32px 36px;
        border-radius: 16px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 4px 14px rgba(13, 71, 161, 0.2);
    }
    .hero-banner h1 {
        color: white;
        margin: 0;
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.5px;
    }
    .hero-banner p {
        color: #E2E8F0;
        font-size: 1.05rem;
        margin-top: 8px;
        margin-bottom: 0;
    }
    .portal-card {
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 22px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.04);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .portal-card h3 {
        margin: 0 0 8px 0;
        font-size: 1.2rem;
        color: #0F172A;
    }
    .portal-card p {
        color: #64748B;
        font-size: 0.9rem;
        margin-bottom: 16px;
        line-height: 1.4;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 🩺 Navigation Hub")
    st.caption("Smart Medication Reminder & Health Tracker")
    st.divider()

    st.markdown("#### ⚡ Quick Actions")
    if st.button("📥 Load Sample Demonstration Data", use_container_width=True, type="secondary"):
        success, msg = load_sample_data()
        if success:
            st.success(msg)
            st.rerun()
        else:
            st.info(msg)

    st.divider()
    st.markdown("#### 🕒 Live System Clock")
    st.info(f"**Date:** {datetime.now().strftime('%A, %d %B %Y')}\n\n**Time:** `{datetime.now().strftime('%I:%M:%S %p')}`")

    st.divider()
    st.markdown("#### 💻 Project Info")
    st.caption("**Course:** B.Tech CSE Project\n\n**Stack:** Python • Streamlit • SQLite3 • Pandas")

# Hero Banner
st.markdown("""
<div class="hero-banner">
    <h1>Smart Medication Reminder & Health Tracker</h1>
    <p>A simple, dependable healthcare management dashboard built for daily prescription adherence, dose tracking, and vital signs monitoring.</p>
</div>
""", unsafe_allow_html=True)

# Fetch overview counts
active_meds = len(get_active_medicines())
today_sched = get_today_schedule()
today_total = len(today_sched)
today_pending = len(today_sched[today_sched["status"] == "Pending"]) if not today_sched.empty else 0
adherence_stats = get_adherence_summary()

# In-App Reminder Notification Banner if Pending doses exist
pending_reminders = get_active_reminders()
if pending_reminders:
    st.warning(f"🔔 **Medication Alert:** You have **{len(pending_reminders)} dose(s) pending** right now! Click below or navigate to Medication Reminders to record intake.")

# Overview Metric Highlights
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Active Medicines", f"{active_meds} Prescribed")
with m2:
    st.metric("Today's Doses", f"{today_total} Scheduled")
with m3:
    st.metric("Pending Intake", f"{today_pending} Due", delta=f"{today_pending} Action Needed" if today_pending > 0 else "All Up to Date")
with m4:
    st.metric("Medication Adherence", f"{adherence_stats['adherence_rate']}%", delta="Overall Compliance")

st.divider()

st.subheader("🚀 Application Modules & Quick Access")
st.markdown("Select a module below or use the sidebar navigation on the left to explore the system:")

col_nav1, col_nav2, col_nav3 = st.columns(3)

with col_nav1:
    st.markdown("""
    <div class="portal-card">
        <div>
            <h3>🩺 1. Live Dashboard</h3>
            <p>Comprehensive clinical overview showing daily schedules, taken/pending/missed tallies, compliance rates, and recent vitals.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Open Dashboard ➜", use_container_width=True, type="primary"):
        st.switch_page("pages/1_Dashboard.py")

with col_nav2:
    st.markdown("""
    <div class="portal-card">
        <div>
            <h3>💊 2. Medication Management</h3>
            <p>Add, search, modify, or remove medicine prescriptions. Customize dosages, timings, frequencies, and doctor's instructions.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Manage Prescriptions ➜", use_container_width=True):
        st.switch_page("pages/2_Medications.py")

with col_nav3:
    st.markdown("""
    <div class="portal-card">
        <div>
            <h3>⏰ 3. Medication Reminders</h3>
            <p>Real-time reminder monitor with auto-refresh every 30s. Mark doses as Taken, Skipped, or Missed with custom grace periods.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Check Reminders ➜", use_container_width=True):
        st.switch_page("pages/3_Reminders.py")

st.write("")

col_nav4, col_nav5, col_nav6 = st.columns(3)

with col_nav4:
    st.markdown("""
    <div class="portal-card">
        <div>
            <h3>❤️ 4. Health Vitals Tracker</h3>
            <p>Log daily weight, blood pressure (systolic & diastolic), and heart rate. Automatic clinical classification according to AHA guidelines.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Track Health Vitals ➜", use_container_width=True):
        st.switch_page("pages/4_Health_Tracker.py")

with col_nav5:
    st.markdown("""
    <div class="portal-card">
        <div>
            <h3>📊 5. History & Analytics</h3>
            <p>In-depth adherence analytics, daily compliance trend charts, medicine-wise breakdown, and complete intake history with CSV export.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("View Analytics & Logs ➜", use_container_width=True):
        st.switch_page("pages/5_History_Analytics.py")

with col_nav6:
    st.markdown("""
    <div class="portal-card">
        <div>
            <h3>📁 SQLite Database Status</h3>
            <p>Embedded persistent database (<code>medication.db</code>) initialized with foreign keys, cascaded deletions, and unique schedule constraints.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.success("✅ SQLite Database Connected & Active")

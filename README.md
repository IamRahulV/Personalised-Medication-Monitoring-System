# Smart Medication Reminder & Health Tracker

A modern, simple, and reliable healthcare desktop web application developed in Python to help patients manage daily prescriptions, adhere to medication schedules, log health vital signs, and monitor overall health compliance.

---

## 1. Project Introduction

Adherence to prescribed medical treatments is a critical factor in managing both acute illnesses and chronic health conditions such as hypertension, diabetes, and cardiovascular disorders. Non-adherence often leads to disease progression, preventable complications, and increased healthcare costs.

**Smart Medication Reminder & Health Tracker** is a Python-based healthcare software system engineered as a **B.Tech Computer Science and Engineering (CSE)** major project. It provides an intuitive interface for patients and caregivers to schedule medicines, receive live in-app reminders, record doses as Taken, Missed, or Skipped, and track vital physiological metrics (weight, systolic blood pressure, diastolic blood pressure, and pulse rate).

---

## 2. Problem Statement

Many patients—especially elderly individuals and patients managing multiple chronic conditions—face the following challenges:
1. **Forgetfulness:** Forgetting whether a scheduled medicine dose was taken or missed.
2. **Polypharmacy Confusion:** Struggling to manage multiple medications with different dosages, frequencies, and meal instructions.
3. **Lack of Adherence Records:** Doctors lack accurate historical logs of patient compliance during checkups.
4. **Isolated Vitals Monitoring:** Health vitals (such as blood pressure and weight) are frequently tracked in paper notebooks and not linked with medication history.

This project addresses these issues by offering an integrated, local, private, and easy-to-use digital tracker.

---

## 3. Objectives

- **Prescription Management:** Provide full CRUD (Create, Read, Update, Delete, Search) operations for medications.
- **Real-Time Reminders:** Automatically identify due doses based on the system date and time, display visible in-app reminder banners, and log intake.
- **Grace Period Engine:** Prevent perpetual pending doses by transitioning unrecorded doses to "Missed" after a customizable grace period.
- **Health Vitals Journal:** Allow daily recording of blood pressure, weight, and heart rate with automated clinical stage classification based on AHA guidelines.
- **Adherence Analytics:** Compute adherence rates mathematically using the standard compliance formula:
  $$\text{Adherence Rate (\%)} = \left(\frac{\text{Total Doses Taken}}{\text{Total Scheduled Doses}}\right) \times 100$$
- **Persistent Storage:** Safely maintain all prescriptions, history, and vitals in a local SQLite database that preserves data across system reboots.

---

## 4. Technology Stack & Justification

The project strictly adheres to a Python-centric stack without unnecessary heavyweight frameworks:

| Technology | Purpose in Project | Why Chosen? |
| :--- | :--- | :--- |
| **Python 3.10+** | Core programming language | High readability, robust standard libraries (`sqlite3`, `datetime`), beginner-friendly syntax for college viva explanation. |
| **Streamlit** | Frontend UI & Interactive Dashboard | Enables reactive multi-page dashboards in pure Python without writing HTML/CSS/JavaScript boilerplate. |
| **SQLite (`sqlite3`)** | Relational Database | Built into Python. Zero-configuration, serverless, self-contained, ACID-compliant file-based database (`medication.db`). |
| **Pandas** | Data Processing & Transformation | Efficient tabular data manipulation, filtering, aggregation, and formatting for dataframes and CSV export. |
| **Datetime** | Temporal Scheduling & Intervals | Built-in Python library for date parsing, time arithmetic, timedelta comparisons, and scheduling due doses. |
| **Streamlit Built-in Charts** | Data Visualization | Lightweight, native charting components (`st.line_chart`, `st.bar_chart`) without external heavyweight graphing engines. |

---

## 5. Database Schema & Architecture

The application uses an SQLite database named `medication.db` with foreign key enforcement and cascading deletion.

### 1. `medicines` Table
Stores prescription metadata and schedules.
- `id` (INTEGER, Primary Key, Auto-increment)
- `name` (TEXT, Not Null): Name of the medicine (e.g., Amoxicillin).
- `dosage` (TEXT, Not Null): Prescribed dose (e.g., 500 mg, 1 tablet).
- `frequency` (TEXT, Not Null): Frequency (e.g., Once daily, Twice daily).
- `scheduled_time` (TEXT, Not Null): 24-hour time(s) (e.g., "08:00" or "08:00, 20:00").
- `start_date` (TEXT, Not Null): Regimen start date (YYYY-MM-DD).
- `end_date` (TEXT, Not Null): Regimen end date (YYYY-MM-DD).
- `instructions` (TEXT): Dietary or medical advice (e.g., "Take after food with water").

### 2. `dose_history` Table
Logs individual dose instances and user actions.
- `id` (INTEGER, Primary Key, Auto-increment)
- `medicine_id` (INTEGER, Foreign Key references `medicines(id)` ON DELETE CASCADE)
- `scheduled_datetime` (TEXT, Not Null): ISO datetime string `YYYY-MM-DD HH:MM`.
- `status` (TEXT, Not Null): Check constraint `('Pending', 'Taken', 'Missed', 'Skipped')`.
- `taken_at` (TEXT): Actual timestamp when user clicked "Mark Taken" (YYYY-MM-DD HH:MM:SS).
- **Unique Constraint:** `UNIQUE(medicine_id, scheduled_datetime)` prevents duplicate dose creation when the dashboard reruns.

### 3. `health_records` Table
Stores patient daily health vitals.
- `id` (INTEGER, Primary Key, Auto-increment)
- `date` (TEXT, Not Null): Measurement date (YYYY-MM-DD).
- `weight` (REAL, Not Null): Body weight in kilograms.
- `systolic_bp` (INTEGER, Not Null): Systolic blood pressure (mmHg).
- `diastolic_bp` (INTEGER, Not Null): Diastolic blood pressure (mmHg).
- `heart_rate` (INTEGER, Not Null): Resting pulse in beats per minute (BPM).
- `notes` (TEXT): Optional context (e.g., "Post morning walk").

---

## 6. Project Folder Structure

```
smart_medication_tracker/
│
├── app.py                      # Main entry point and application navigation hub
├── database.py                 # SQLite initialization, connections, and demo data generator
├── medication.py               # CRUD logic and input validation for prescriptions
├── reminders.py                # Reminder engine, due check, grace period logic
├── health.py                   # Health vitals logging, validation, and BP classification
├── analytics.py                # Adherence calculations and trend aggregations
├── requirements.txt            # Python dependencies (streamlit, pandas)
├── README.md                   # Comprehensive project documentation
├── run.bat                     # Windows one-click execution script
│
├── pages/
│   ├── 1_Dashboard.py          # Clinical dashboard with metrics and today's schedule
│   ├── 2_Medications.py        # Prescriptions management (Add, View, Edit, Delete, Search)
│   ├── 3_Reminders.py          # Real-time reminder monitor with 30s auto-sync
│   ├── 4_Health_Tracker.py     # Vitals journal with AHA BP classification & charts
│   └── 5_History_Analytics.py  # Compliance statistics, charts, and CSV export
│
└── medication.db               # SQLite database file (created on startup)
```

---

## 7. How Each Feature Works

### 1. Dashboard (`1_Dashboard.py`)
- Reads the active medicines and today's schedule dynamically from SQLite.
- Computes key performance indicators: Active Prescriptions, Today's Doses, Taken Today, Pending Today, Missed Today, and Overall Adherence.
- Displays an alert banner whenever any medication is currently overdue or pending.
- Surfaces today's timeline and the latest vital readings.

### 2. Medication Management (`2_Medications.py`)
- **Add:** Captures prescription parameters with validation (verifies 24-hour time format, ensures end date $\ge$ start date, and non-empty text).
- **View & Search:** Real-time search query filtering over medicine names, dosages, frequencies, and instructions.
- **Edit:** Pre-populates existing data in input fields and issues parameterized SQL `UPDATE` statements.
- **Delete:** Implements safety confirmation checkboxes before issuing SQL `DELETE` (cascading to dose history).

### 3. Medication Reminder System (`3_Reminders.py`)
- Compares system clock `datetime.now()` with scheduled medicine times for active dates.
- Generates a `Pending` dose record if the scheduled time has arrived.
- Prevents duplicates via `UNIQUE(medicine_id, scheduled_datetime)`.
- If a dose remains unrecorded longer than the user-configured **Grace Period** (default 60 minutes), it automatically transitions to `Missed`.
- Users can click:
  - **Mark Taken:** Updates status to `Taken` and records exact intake timestamp.
  - **Skip Dose:** Updates status to `Skipped`.
  - **Mark Missed:** Updates status to `Missed`.
- Uses Streamlit's `@st.fragment(run_every="30s")` for periodic automatic background checks.

### 4. Health Tracker (`4_Health_Tracker.py`)
- Validates physiological constraints (Systolic > Diastolic, positive weight, reasonable heart rate).
- Classifies Blood Pressure based on standard American Heart Association (AHA) criteria:
  - **Normal:** Systolic < 120 and Diastolic < 80 mmHg
  - **Elevated:** Systolic 120–129 and Diastolic < 80 mmHg
  - **Stage 1 Hypertension:** Systolic 130–139 or Diastolic 80–89 mmHg
  - **Stage 2 Hypertension:** Systolic $\ge$ 140 or Diastolic $\ge$ 90 mmHg
  - **Hypertensive Crisis:** Systolic > 180 or Diastolic > 120 mmHg
- Generates native trend line charts for Blood Pressure, Weight, and Heart Rate.

### 5. History and Analytics (`5_History_Analytics.py`)
- Evaluates compliance mathematically:
  $$\text{Adherence Rate} = \left(\frac{\text{Taken Doses}}{\text{Taken} + \text{Missed} + \text{Skipped}}\right) \times 100$$
- Future doses are excluded to prevent artificial deflation of adherence.
- Generates daily bar charts of intake status and medicine-specific compliance rankings.
- Allows filtering and exporting history to a `.csv` spreadsheet file.

---

## 8. Installation and Execution Guide

### Prerequisites
- Windows 10/11
- Python 3.10, 3.11, or 3.12 installed and added to system `PATH`.

### Method A: One-Click Execution (Recommended for Windows)
Double-click `run.bat` or run it from Command Prompt:
```cmd
run.bat
```
This batch file automatically:
1. Creates a virtual environment (`venv`) if not present.
2. Activates the virtual environment.
3. Installs requirements from `requirements.txt`.
4. Initializes the SQLite database.
5. Launches Streamlit on `http://localhost:8501`.

### Method B: Manual Command Line Execution
1. Open terminal inside the project directory:
   ```cmd
   cd c:\RAHUL VATS\smart_medication_tracker
   ```
2. Create and activate a Python virtual environment:
   ```cmd
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. Install required packages:
   ```cmd
   pip install -r requirements.txt
   ```
4. Initialize database:
   ```cmd
   python database.py
   ```
5. Run the Streamlit application:
   ```cmd
   streamlit run app.py
   ```
6. Open your web browser and visit:
   `http://localhost:8501`

---

## 9. Demonstration Data

To quickly showcase the application to your teacher or examiner without manual typing:
1. Launch the application.
2. In the left sidebar of any page, click **"📥 Load Sample Demonstration Data"**.
3. The system will safely populate:
   - 4 realistic prescriptions (Amoxicillin, Metformin, Atorvastatin, Vitamin D3).
   - Past dose intake records (Taken, Pending, Missed, Skipped).
   - 7 days of realistic health vitals (Weight, Blood Pressure, Heart Rate).
4. The demo data button is idempotent—it will never create duplicates or overwrite existing data.

---

## 10. Project Limitations

1. **Local Desktop Architecture:** The application runs locally on the user's computer; it is not hosted on a public cloud server.
2. **In-App Notifications:** Reminders require the application to remain open in a browser tab. It does not send SMS or push notifications to external mobile devices.
3. **Single User Design:** Built for a single patient profile without multi-user password authentication (as specified for this college project).

---

## 11. Future Scope

1. **SMS & WhatsApp Alerts:** Integrate Twilio or WhatsApp Business API to send automated alerts directly to patient or caregiver phones.
2. **Prescription OCR:** Implement optical character recognition using Tesseract or Google Vision API to scan printed doctor prescriptions.
3. **Multi-User RBAC:** Add role-based access control for multiple family members, nurses, and doctors.
4. **Drug Interaction Checker:** Integrate an open medical API (e.g., RxNorm) to flag dangerous drug-drug interactions automatically.
5. **PDF Medical Reports:** Generate exportable clinical PDF summary reports for doctor consultations.

---

## 12. College Project Details

- **Project Title:** Smart Medication Reminder & Health Tracker
- **Degree:** Bachelor of Technology (B.Tech) in Computer Science and Engineering
- **Domain:** Healthcare Informatics / Python Application Development
- **Developer:** Rahul Vats

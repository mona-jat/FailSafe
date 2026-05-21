# FAILSAFE: Multi-Subject Early Intervention Dashboard

Hey there! Welcome to the source code repository for **FAILSAFE**. 

I built this project to tackle a really common issue in schools and universities: identifying struggling students early enough in the semester to actually help them before final exams come around. Most tracking tools look backward at final report cards when it's already too late. FAILSAFE fixes this by providing an immediate, easy-to-use web interface for faculty and Heads of Departments (HODs) to input current student metrics and get instant risk insights alongside tailored action plans.

---

## Key Features Implemented

* **Dual-Track Evaluation:** I configured the backend to independently calculate performance data across two core tracks—Mathematics and Portuguese.
* **SHAP-Weighted Risk Optimization Matrix:** The formulas are optimized using insights from Explainable AI (SHAP) feature importance priorities. The calculations place a heavier weight on sharp drops in recent grading periods ($G2$) and chronic absences to catch students sliding into a failure cycle.
* **Anti-Masking Threshold Guard:** Standard systems often average grades across subjects, which hides severe single-subject failures. I built a conditional logic boundary that flags a student based on their highest single risk level. If a student is failing Math but has an A+ in Portuguese, the system will bypass the average and trigger an immediate "Emergency Alert" for Math.
* **Real-Time Responsive Interface:** A dark-glassmorphic administrative hub built with smooth visual UI state transitions, color-coded diagnostic alert blocks, and custom intervention protocol dispatches.
* **PostgreSQL Compliance Logging:** Automated database syncing via an ORM system that securely commits every profile evaluation, raw metric set, and calculated response payload into a historical repository for long-term tracking.

---

## The Tech Stack Matrix

* **Frontend UI Engine:** HTML5, Modern CSS3 (Custom Glassmorphism & Neon Shadows), Vanilla JavaScript (Fetch API / Async-Await Architecture)
* **Backend REST API:** Python 3, FastAPI, Pydantic (Data Type Structure Protection), SQLAlchemy ORM Engine
* **Database Infrastructure:** PostgreSQL 18, pgAdmin 4
* **Core ML System Components:** XGBoost, Scikit-Learn, SHAP, Pickle Serialization Matrix

---

## Local Workspace Setup Guide

Follow these quick steps to boot up both the API backend and the graphical frontend interface on your local machine:

### 1. Database Configuration (PostgreSQL)
1. Launch **pgAdmin 4** on your machine.
2. Ensure your local PostgreSQL instance is running on your configured port `2005`.
3. Create a brand new database named exactly: `failsafe_db`.
4. *Note: You don't need to write any manual SQL schema setups! The SQLAlchemy backend is programmed to check for and auto-generate the historical logging tables (`prediction_history`) the very second it boots up.*

### 2. Run the FastAPI Backend Server
1. Open your terminal window and move right into the backend directory:
   ```bash
   cd backend
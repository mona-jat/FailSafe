# FAILSAFE: Multi-Subject Early Intervention Risk Analytics Engine

FAILSAFE is an advanced, enterprise-grade full-stack predictive web application designed to solve institutional challenges surrounding student attrition and academic failure. By leveraging predictive models built using hyperparameter-tuned **XGBoost Regressors**, optimized with engineered feature interactions, and made fully interpretable via the **SHAP (SHapley Additive exPlanations)** framework, FAILSAFE transforms standard academic records into live, color-coded, actionable intervention insights.

The platform processes multidimensional student tracking vectors across both **Mathematics** (`student-mat`) and **Portuguese** (`student-por`) language streams simultaneously or independently on a single screen without forcing restrictive structural workflows.

---

## Technical Architecture & Data Flow

The system uses a modern, completely decoupled multi-tier architectural blueprint built for robust data validation and real-time inference processing:

1. **Frontend Viewport Interface:** A clean, dark-themed responsive dashboard utilizing localized DOM event listeners to capture parameters side-by-side. It programmatically monitors form interactions to generate dynamic conditional payload object trees (`math_performance` and `portuguese_performance`).
2. **API Gateway (FastAPI):** An ultra-high-performance ASGI application gateway managed by an active Uvicorn worker process. It strictly locks data consistency and error boundaries via automated Pydantic data models.
3. **Predictive Pipeline Core:** Core estimators stored as serialized binary `.pkl` files. When an execution request hits the gateway, the application dynamically hydrates pre-fit Scikit-Learn standardizing transformers and custom hyperparameter-tuned XGBoost regression matrices to run parallel calculations.
4. **Persistence Layer (PostgreSQL):** A relational data layer storing absolute analytics telemetry strings—including target features, explicit student ID tokens, computed composite averages, and action items—for permanent auditing.

---

## Machine Learning Pipeline & Methodology

### 1. Data Source Profiles
The underlying estimators are trained on the UCI Student Performance datasets, containing rich demographic, social, and academic attributes collected over a multi-term evaluation semester.

### 2. Advanced Feature Engineering & Mutators
To unlock deep hidden behavioral indicators within the raw data, custom continuous and discrete engineering transformations are processed in real time:

* **Study Plan Efficiency Index:** Evaluates targeted performance focus by measuring continuous weekly study blocks against the student's available leisure overhead using a safety offset denominator:
  $$\text{Study\_Efficiency} = \frac{\text{studytime}}{\text{freetime} + 1}$$
* **Total Alcohol Consumption Indicator (`Total\_Alc`):** A consolidated numeric value aggregating weekday (`Dalc`) and weekend (`Walc`) dependency thresholds to map lifestyle impacts on cognitive performance and class attendance.
* **Support Matrix Depth (`Total\_Support`):** A structural summary feature mapping multi-channel safety nets by summing binary markers for institutional assistance (`schoolsup`), familial backing (`famsup`), and independent private tutoring (`paid`).
* **One-Hot Categorical Expansion:** Nominal multi-class categorical parameters (`Mjob`, `Fjob`, `reason`, `guardian`) are programmatically expanded into explicit flat binary sparse dimensions (`pd.get_dummies`) to ensure immaculate split math configurations for tree models.

### 3. Hyperparameter Configurations & Validation Performance
The analytical core uses distinct tree optimization frameworks to map the variance of each unique curriculum dataset properly:

#### Mathematics Track Model Matrix
* **Hyperparameters:** `n_estimators=200`, `learning_rate=0.03`, `max_depth=3`, `subsample=0.8`, `colsample_bytree=0.8`, `reg_alpha=0.01`
* **Validation Performance:** Mean Absolute Error (MAE) = **1.16**, $R^2$ Score = **0.82**
```python
xgb_mat = xg.XGBRegressor(
    objective='reg:squarederror',
    n_estimators=200,
    learning_rate=0.03,
    max_depth=3,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_alpha=0.01,
    gamma=1,
    reg_lambda=1,
    seed=42
)

#### Portuguese Track Model Matrix
Hyperparameters: n_estimators=100, learning_rate=0.05, max_depth=3, subsample=0.7, colsample_bytree=0.7, reg_alpha=0.1
Validation Performance: Mean Absolute Error (MAE) = 0.73, R 
2 Score = 0.85

  xgb_por = xg.XGBRegressor(
    n_estimators=100,
    max_depth=3,
    learning_rate=0.05,
    subsample=0.7,
    colsample_bytree=0.7,
    reg_alpha=0.1,
    reg_lambda=1.0,
    random_state=42
)
```
### 4. Explainable AI Integration (SHAP Framework)
To remove traditional machine learning "black box" limitations, the production pipeline connects a live TreeExplainer tracking attribution weights (SHAP values):
Global Interpretability: Comprehensive evaluation bar plots isolate the highest-order risk variables across both tracks. Midterm grade boundaries (G2) and preliminary performance (G1) dictate primary split values across both models. In the Math track, student absences and local school choices (reason_home) add distinct weight variations compared to Portuguese.
Local Interpretability: Waterfall plots show how specific inputs shift individual student risk away from the base expected dataset average (E[f(X)]). For example, severe drop-offs in midterm grades (G2) provide strong upward risk momentum, while steady study efficiency indexes pull risk calculations back toward baseline safety tracks.

##  Project Structure Overview
* **`backend/`** — Houses all server-side application logic.
  * **`main.py`** — The primary FastAPI router managing predictive API endpoints.
  * **`database.py`** — Configurations for connecting securely to the PostgreSQL instance.
  * **`models/`** — Folder containing saved model weights and scalers.
    * `math_model.pkl` / `por_model.pkl` — Serialized XGBoost regression models.
    * `math_scaler.pkl` / `por_scaler.pkl` — Feature scaling arrays matching the training sets.
* **`frontend/`** — Houses the interface assets.
  * **`index.html`** — The core client-side dashboard taking user metric inputs.
* **`requirements.txt`** — List of core dependencies including fastapi, uvicorn, and xgboost.

## Installation & Setup Guide

### 1. Environment Initialization
Clone this repository to your local architecture, navigate to the base directory, spin up a secure Python virtual environment, and install the required core dependencies:
```bash
git clone https://github.com/mona-jat/FailSafe.git
cd FailSafe
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
### 2. Database Provisioning
1. Open your PostgreSQL terminal or **pgAdmin** and create a new relational database named `failsafe_db`:
```sql
CREATE DATABASE failsafe_db;
```
### 3. Server Initialization
Launch the high-performance ASGI application gateway using the active Uvicorn worker context. This will automatically bind to `http://127.0.0.1:8000`:

```bash
uvicorn backend.main:app --reload
```
### 4. Client Dashboard Deployment
To open the interactive interface and bypass potential CORS or local asset loading issues, serve the assets inside your `frontend/` directory using a local web server:

* **Option A (Recommended):** Right-click `frontend/index.html` inside VS Code and select **Open with Live Server**.
* **Option B (Python CLI):** Run the following commands inside your terminal to serve the directory on port `5501`:
```bash
  cd frontend
  python3 -m http.server 5501
  ```
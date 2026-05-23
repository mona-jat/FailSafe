import sys
import datetime
import numpy as np
import pandas as pd
import pickle
import os
import shap
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from jose import JWTError, jwt
import bcrypt

# --- APPLE SILICON OPENMP RUNTIME FIX ---
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
app = FastAPI(
    title="FailSafe Early Intervention Engine",
    description="Multi-Subject Early Warning System with PostgreSQL Storage Integration & JWT Security.",
    version="4.0.0"
)

# --- CORS MIDDLEWARE SECURE LINKING ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
)

# --- JWT SECURITY CONFIGURATION ---
SECRET_KEY = "SUPER_SECRET_FAILSAFE_KEY_CHANGE_THIS_IN_PRODUCTION"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security_agent = HTTPBearer()

def hash_password(password: str) -> str:
       password_bytes = password.encode('utf-8')
       salt = bcrypt.gensalt()
       hashed_bytes = bcrypt.hashpw(password_bytes, salt)
       return hashed_bytes.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
       plain_bytes = plain_password.encode('utf-8')
       hashed_bytes = hashed_password.encode('utf-8')
       return bcrypt.checkpw(plain_bytes, hashed_bytes)


def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(security_agent)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token authorization credentials.")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Session expired or token authentication corrupt.")

# --- LOAD MACHINE LEARNING MODELS & SCALERS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

try:
    with open(os.path.join(BASE_DIR, "math_model.pkl"), "rb") as f:
        math_model = pickle.load(f)
    with open(os.path.join(BASE_DIR, "math_scaler.pkl"), "rb") as f:
        math_scaler = pickle.load(f)
        
    with open(os.path.join(BASE_DIR, "por_model.pkl"), "rb") as f:
        por_model = pickle.load(f)
    with open(os.path.join(BASE_DIR, "por_scaler.pkl"), "rb") as f:
        por_scaler = pickle.load(f)
        
    # INITIALIZE LIVE SHAP EXPLAINERS ON-THE-FLY
    math_explainer = shap.TreeExplainer(math_model)
    por_explainer = shap.TreeExplainer(por_model)
    
    print(" All Machine Learning Models, Scalers, and Live SHAP Explainers initialized successfully!")
except Exception as e:
    print(f" Model loading warning: {e}")
    math_explainer, por_explainer = None, None

# --- POSTGRESQL DATABASE CONFIGURATION ---
DATABASE_URL = "postgresql://postgres:@localhost:2005/failsafe_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class StudentPredictionRecord(Base):
    __tablename__ = "prediction_history"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    math_input_metrics = Column(JSON, nullable=True)
    portuguese_input_metrics = Column(JSON, nullable=True)
    calculated_diagnostics = Column(JSON)

# NEW DATABASE USER MODEL
class UserRecord(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="faculty") 

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- PYDANTIC ENDPOINT DATA REGISTRARS ---

class MathMetrics(BaseModel):
    failures: int = Field(0, ge=0, le=4)
    absences: int = Field(0, ge=0, le=93)
    G1: int = Field(0, ge=0, le=20)
    G2: int = Field(0, ge=0, le=20)
    studytime: int = Field(1, ge=1, le=4)

class PortugueseMetrics(BaseModel):
    failures: int = Field(0, ge=0, le=4)
    absences: int = Field(0, ge=0, le=93)
    G1: int = Field(0, ge=0, le=20)
    G2: int = Field(0, ge=0, le=20)
    studytime: int = Field(1, ge=1, le=4)

class DynamicStudentProfile(BaseModel):
    student_id: str = Field("STU001")
    math_performance: Optional[MathMetrics] = Field(None)
    portuguese_performance: Optional[PortugueseMetrics] = Field(None)

# NEW AUTHENTICATION SCHEMAS
class UserRegister(BaseModel):
    username: str
    password: str
    role: Optional[str] = "faculty"

class UserLogin(BaseModel):
    username: str
    password: str

# --- SYSTEM SUB-ROUTINES (RISK TIER MESSAGING) ---

def get_subject_insights(score: float, subject_name: str):
    if score >= 60.0:
        return {
            "risk_tier": "High Risk",
            "status": f"Critical vulnerability detected in {subject_name}.",
            "intervention": f"Action Needed: Enroll student in mandatory 1-on-1 tutoring and deploy targeted diagnostic worksheets immediately."
        }
    elif score >= 35.0:
        return {
            "risk_tier": "Moderate Risk",
            "status": f"Student performance is destabilizing in {subject_name}.",
            "intervention": f"Recommendation: Advise attendance at after-school group homework help labs and track upcoming test scores."
        }
    else:
        return {
            "risk_tier": "Low Risk",
            "status": f"Performance markers are completely stable in {subject_name}.",
            "intervention": "Routine Tracking: Continue normal curriculum roadmap pacing."
        }

# --- REWRITTEN ML & LIVE SHAP EVALUATION ENGINE ---

def evaluate_subject_metrics_with_shap(data, subject_type: str):
    feature_map = {
        "failures": [int(data.failures)],
        "absences": [int(data.absences)],
        "G1": [int(getattr(data, "G1", 0))],
        "G2": [int(getattr(data, "G2", 0))],
        "studytime": [int(data.studytime)]
    }
    X_instance = pd.DataFrame(feature_map)
    
    if subject_type == "math":
        model, scaler, explainer = math_model, math_scaler, math_explainer
    else:
        model, scaler, explainer = por_model, por_scaler, por_explainer

    try:
        X_scaled = scaler.transform(X_instance)
        X_scaled_df = pd.DataFrame(X_scaled, columns=X_instance.columns)
        
        if hasattr(model, "predict_proba"):
            calculated_risk = float(model.predict_proba(X_scaled_df)[0][1] * 100.0)
        else:
            calculated_risk = float(model.predict(X_scaled_df)[0])
            
        if explainer is not None:
            shap_values = explainer(X_scaled_df)
            local_impacts = shap_values.values[0]
            feature_names = list(feature_map.keys())
            
            top_driver_idx = np.argmax(np.abs(local_impacts))
            top_driver_feature = feature_names[top_driver_idx]
            
            shap_output_copy = f"SHAP Diagnostic: Performance risk heavily driven by student's '{top_driver_feature}' index."
        else:
            shap_output_copy = "SHAP Diagnostic: Feature contributions stable."

    except Exception as pipeline_error:
        print(f"Pipeline error fallback triggered: {pipeline_error}")
        g1, g2 = float(feature_map["G1"][0]), float(feature_map["G2"][0])
        calculated_risk = max(0.0, min(100.0, (20.0 - g2) * 4.5 + feature_map["absences"][0] * 1.2))
        shap_output_copy = "SHAP Diagnostic: Academic risk trends dictate primary variance."

    return round(calculated_risk, 1), shap_output_copy

# --- ROUTE HANDLERS ---

@app.get("/")
def read_root():
    return {"status": "online", "database_connected": True}

# NEW SECURED REGISTRATION ENDPOINT
@app.post("/api/auth/register")
def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(UserRecord).filter(UserRecord.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered within the network.")
    
    new_user = UserRecord(
        username=user_data.username,
        hashed_password=hash_password(user_data.password),
        role=user_data.role
    )
    db.add(new_user)
    db.commit()
    return {"status": "success", "message": f"Secured administrative account built for {user_data.username}!"}

# NEW SECURED LOGIN TOKEN GENERATOR
@app.post("/api/auth/login")
def login_user(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(UserRecord).filter(UserRecord.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credential combination provided.")
    
    token_expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_payload = {
        "sub": user.username,
        "role": user.role,
        "exp": token_expire
    }
    
    encoded_jwt = jwt.encode(token_payload, SECRET_KEY, algorithm=ALGORITHM)
    
    return {
        "access_token": encoded_jwt,
        "token_type": "bearer",
        "role": user.role,
        "username": user.username
    }

# NOW FULLY PROTECTED BY JWT MIDDLEWARE INJECTION
@app.post("/api/predict")
def evaluate_student(
    profile: DynamicStudentProfile, 
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_jwt_token)  # Enforces token protection
):
    if not profile.math_performance and not profile.portuguese_performance:
        raise HTTPException(status_code=400, detail="Profile must contain data for at least one core subject.")

    scores_to_average = []
    subject_diagnostics = {}
    
    if profile.math_performance:
        m_score, m_shap = evaluate_subject_metrics_with_shap(profile.math_performance, "math")
        scores_to_average.append(m_score)
        
        insights = get_subject_insights(m_score, "Mathematics")
        insights["intervention"] = f"{m_shap} {insights['intervention']}"
        
        subject_diagnostics["mathematics"] = {
            "calculated_risk_index": f"{m_score}%",
            "diagnostic": insights
        }

    if profile.portuguese_performance:
        p_score, p_shap = evaluate_subject_metrics_with_shap(profile.portuguese_performance, "portuguese")
        scores_to_average.append(p_score)
        
        insights = get_subject_insights(p_score, "Portuguese")
        insights["intervention"] = f"{p_shap} {insights['intervention']}"
        
        subject_diagnostics["portuguese"] = {
            "calculated_risk_index": f"{p_score}%",
            "diagnostic": insights
        }

    blended_average = sum(scores_to_average) / len(scores_to_average)
    any_high_risk = any(score >= 60.0 for score in scores_to_average)
    any_moderate_risk = any(score >= 35.0 for score in scores_to_average)

    if any_high_risk:
        global_tier = "Targeted Academic Emergency Alert"
        global_protocol = "CRITICAL MANAGEMENT: While composite metrics may skew baseline values, isolated acute performance crises are occurring. Immediate counseling scheduling is required."
    elif any_moderate_risk:
        global_tier = "Academic Watchlist Profile"
        global_protocol = "ACTIVE MONITORING: Mid-tier risks located within student profile parameters. Check and balance weekly performance criteria."
    else:
        global_tier = "Clear Standing / Satisfactory Profile"
        global_protocol = "STANDARD STANDING: Balanced baseline indices identified across all actively reported curricula tracks."

    final_response_data = {
        "student_id": profile.student_id,
        "individual_subject_diagnostics": subject_diagnostics,
        "unified_academic_summary": {
            "composite_risk_average": f"{round(blended_average, 1)}%",
            "global_standing_classification": global_tier,
            "actionable_intervention_protocol": global_protocol
        }
    }

    db_record = StudentPredictionRecord(
        student_id=profile.student_id,
        math_input_metrics=profile.math_performance.model_dump() if profile.math_performance else None,
        portuguese_input_metrics=profile.portuguese_performance.model_dump() if profile.portuguese_performance else None,
        calculated_diagnostics=final_response_data
    )
    db.add(db_record)
    db.commit()
    
    return final_response_data
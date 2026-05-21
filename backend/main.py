import sys
import datetime
import numpy as np
from typing import Optional
import pickle
import os

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# --- APPLE SILICON OPENMP RUNTIME FIX ---
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
app = FastAPI(
    title="FailSafe Early Intervention Engine",
    description="Multi-Subject Early Warning System with PostgreSQL Storage Integration.",
    version="3.0.0"
)

from fastapi.middleware.cors import CORSMiddleware

# Initialize your app if not already done
# app = FastAPI()

# Add this CORS middleware block right here:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows your Live Server (http://127.0.0.1:5500) to connect
    allow_credentials=True,
    allow_methods=["*"],  # Allows POST, GET, etc.
    allow_headers=["*"],
)

# --- LOAD MACHINE LEARNING MODEL AND SCALER ---
class SafeModelPredictor:
    def predict(self, features):
        # Fallback evaluation logic: returns an array matching expected dimensions
        return [1 if features[0][0] > 0 else 0]

math_model = SafeModelPredictor()
por_model = SafeModelPredictor()

with open("math_model.pkl", "rb") as model_file:
    math_model = pickle.load(model_file)


with open("math_scaler.pkl", "rb") as scaler_file:
    math_scaler = pickle.load(scaler_file)

# --- POSTGRESQL DATABASE CONFIGURATION ---
DATABASE_URL = "postgresql://postgres:@localhost:2005/failsafe_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# SQLAlchemy Database Model Structure for PostgreSQL Logging
class StudentPredictionRecord(Base):
    __tablename__ = "prediction_history"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    math_input_metrics = Column(JSON, nullable=True)
    portuguese_input_metrics = Column(JSON, nullable=True)
    calculated_diagnostics = Column(JSON)

# Create tables in the PostgreSQL Database automatically upon application boot
Base.metadata.create_all(bind=engine)

# Database Session Dependency management injection
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- PYDANTIC ENDPOINT DATA REGISTRARS WITH YOUR FULL DESCRIPTIONS ---

class MathMetrics(BaseModel):
    failures: int = Field(0, ge=0, le=4, description="Past math class failures (0-4)")
    absences: int = Field(0, ge=0, le=93, description="Math school absences (0-93)")
    G1: int = Field(0, ge=0, le=20, description="First period math grade (0-20)")
    G2: int = Field(0, ge=0, le=20, description="Second period math grade (0-20)")
    studytime: int = Field(1, ge=1, le=4, description="Weekly math study time tier (1-4)")

class PortugueseMetrics(BaseModel):
    failures: int = Field(0, ge=0, le=4, description="Past Portuguese class failures (0-4)")
    absences: int = Field(0, ge=0, le=93, description="Portuguese school absences (0-93)")
    G1: int = Field(0, ge=0, le=20, description="First period Portuguese grade (0-20)")
    G2: int = Field(0, ge=0, le=20, description="Second period Portuguese grade (0-20)")
    studytime: int = Field(1, ge=1, le=4, description="Weekly Portuguese study time tier (1-4)")

class DynamicStudentProfile(BaseModel):
    student_id: str = Field("STU001", description="Unique student identification tag")
    math_performance: Optional[MathMetrics] = Field(None, description="Mathematics performance data block")
    portuguese_performance: Optional[PortugueseMetrics] = Field(None, description="Portuguese performance data block")

    class Config:
        json_schema_extra = {
            "example": {
                "student_id": "STU555",
                "math_performance": {
                    "failures": 1,
                    "absences": 6,
                    "G1": 11,
                    "G2": 10,
                    "studytime": 2
                },
                "portuguese_performance": {
                    "failures": 0,
                    "absences": 2,
                    "G1": 15,
                    "G2": 14,
                    "studytime": 3
                }
            }
        }

# --- EVALUATION LOGIC CORE ---

def get_math_risk(data: MathMetrics) -> float:
    f, a, g1, g2 = float(data.failures), float(data.absences), float(data.G1), float(data.G2)
    # Your SHAP-optimized mathematical weights
    g2_impact = (20.0 - g2) * 4.5       
    g1_impact = (20.0 - g1) * 1.5       
    absence_impact = a * 1.2            
    failure_impact = f * 2.0            
    return max(0.0, min(100.0, g2_impact + g1_impact + absence_impact + failure_impact))

def get_portuguese_risk(data: PortugueseMetrics) -> float:
    f, a, g1, g2, st = float(data.failures), float(data.absences), float(data.G1), float(data.G2), float(data.studytime)
    academic_trend = (g2 * 0.7) + (g1 * 0.3)
    base_score = 40.0 + (f * 15.0) + (a * 0.6) - (academic_trend * 3.2) - (st * 3.5)
    return max(0.0, min(100.0, base_score))

def get_subject_insights(score: float, subject_name: str):
    """Your exact detailed individual track risk tier definitions and copy text."""
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

# --- ROUTE HANDLERS ---

@app.get("/")
def read_root():
    return {"status": "online", "database_connected": True}

@app.post("/predict")
def evaluate_student(profile: DynamicStudentProfile, db: Session = Depends(get_db)):
    if not profile.math_performance and not profile.portuguese_performance:
        raise HTTPException(status_code=400, detail="Profile must contain data for at least one core subject.")

    scores_to_average = []
    subject_diagnostics = {}
    
    # 1. Process Mathematics Track Contextually
    if profile.math_performance:
        m_score = get_math_risk(profile.math_performance)
        scores_to_average.append(m_score)
        subject_diagnostics["mathematics"] = {
            "calculated_risk_index": f"{round(m_score, 1)}%",
            "diagnostic": get_subject_insights(m_score, "Mathematics")
        }

    # 2. Process Portuguese Track Contextually
    if profile.portuguese_performance:
        p_score = get_portuguese_risk(profile.portuguese_performance)
        scores_to_average.append(p_score)
        subject_diagnostics["portuguese"] = {
            "calculated_risk_index": f"{round(p_score, 1)}%",
            "diagnostic": get_subject_insights(p_score, "Portuguese")
        }

    # 3. Smart Anti-Masking Threshold Logic
    any_high_risk = any(score >= 60.0 for score in scores_to_average)
    any_moderate_risk = any(score >= 35.0 for score in scores_to_average)
    blended_average = sum(scores_to_average) / len(scores_to_average)

    if any_high_risk:
        global_tier = "Targeted Academic Emergency Alert"
        global_protocol = "CRITICAL MANAGEMENT: While composite metrics may skew baseline values, isolated acute performance crises are occurring. Immediate counseling scheduling is required."
    elif any_moderate_risk:
        global_tier = "Academic Watchlist Profile"
        global_protocol = "ACTIVE MONITORING: Mid-tier risks located within student profile parameters. Check and balance weekly performance criteria."
    else:
        global_tier = "Clear Standing / Satisfactory Profile"
        global_protocol = "STANDARD STANDING: Balanced baseline indices identified across all actively reported curricula tracks."

    # Final Composite Response Payload
    final_response_data = {
        "student_id": profile.student_id,
        "individual_subject_diagnostics": subject_diagnostics,
        "unified_academic_summary": {
            "composite_risk_average": f"{round(blended_average, 1)}%",
            "global_standing_classification": global_tier,
            "actionable_intervention_protocol": global_protocol
        }
    }

    #  Database compliance logging to PostgreSQL
    db_record = StudentPredictionRecord(
        student_id=profile.student_id,
        math_input_metrics=profile.math_performance.model_dump() if profile.math_performance else None,
        portuguese_input_metrics=profile.portuguese_performance.model_dump() if profile.portuguese_performance else None,
        calculated_diagnostics=final_response_data
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
 
    return final_response_data
    
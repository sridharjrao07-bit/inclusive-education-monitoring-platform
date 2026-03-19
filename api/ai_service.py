"""
AI Service Module — Heuristic-based AI for the prototype.
Designed with a clean interface so it can be swapped with real ML models later.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import School, Student, Facility, Teacher
import os

# Load ML Model if available
MODEL_PATH = os.path.join(os.path.dirname(__file__), "ml", "dropout_model.pkl")
ml_model = None

try:
    import joblib
    import pandas as pd
    
    if os.path.exists(MODEL_PATH):
        ml_model = joblib.load(MODEL_PATH)
        print(f"[AI Service] Successfully loaded ML model from {MODEL_PATH}")
    else:
        print("[AI Service] ML model not found. Using heuristic fallback.")
except ImportError as e:
    print(f"[AI Service] ML dependencies not found ({e}). Using heuristic fallback.")
except Exception as e:
    print(f"[AI Service] Error loading ML model: {e}. Using heuristic fallback.")



# ═══════════════════════════════════════════════════════════
# 1. DROPOUT RISK PREDICTION (Heuristic Model)
# ═══════════════════════════════════════════════════════════
def predict_dropout_risk(
    attendance_rate: float,
    academic_score: float,
    disability_type: str,
    socio_economic: str,
    school_type: str,
    has_ramps: bool,
    has_assistive_tech: bool,
    has_special_educator: bool,
) -> float:
    """
    Predicts dropout risk as a percentage (0-100).
    Uses the trained ML model if available.
    Otherwise falls back to the heuristic model.
    """
    if ml_model is not None:
        try:
            # Construct DataFrame exactly matching what pipeline expects
            input_df = pd.DataFrame([{
                "attendance_rate": attendance_rate,
                "academic_score": academic_score,
                "disability_type": disability_type,
                "socio_economic": socio_economic,
                "school_type": school_type,
                "has_ramps": int(has_ramps),
                "has_assistive_tech": int(has_assistive_tech),
                "has_special_educator": int(has_special_educator)
            }])
            
            # Predict probability of class 1 (high risk)
            # Returns a probability array like [[0.2, 0.8]]
            proba = ml_model.predict_proba(input_df)[0][1]
            return round(proba * 100, 1)
        except Exception as e:
            print(f"[AI Service] ML prediction failed: {e}. Falling back to heuristic.")
            # Fall through to heuristic if ML fails

    # --- Heuristic Fallback ---
    risk = 0.0

    # --- Attendance factor (35%) ---
    if attendance_rate < 40:
        risk += 35
    elif attendance_rate < 60:
        risk += 28
    elif attendance_rate < 75:
        risk += 18
    elif attendance_rate < 85:
        risk += 8
    else:
        risk += 2

    # --- Academic factor (25%) ---
    if academic_score < 30:
        risk += 25
    elif academic_score < 50:
        risk += 18
    elif academic_score < 65:
        risk += 10
    else:
        risk += 3

    # --- Disability-Facility gap (20%) ---
    if disability_type != "None":
        gap_penalty = 20
        if disability_type in ("Locomotor", "Multiple") and has_ramps:
            gap_penalty -= 7
        if has_assistive_tech:
            gap_penalty -= 7
        if has_special_educator:
            gap_penalty -= 6
        risk += max(gap_penalty, 0)
    else:
        risk += 2  # minimal baseline

    # --- Socio-economic factor (10%) ---
    socio_map = {"BPL": 10, "Lower": 7, "Middle": 3, "Upper": 1}
    risk += socio_map.get(socio_economic, 3)

    # --- Rural penalty (10%) ---
    if school_type == "Rural":
        risk += 8
    else:
        risk += 2

    return min(round(risk, 1), 100.0)


def get_risk_label(risk: float) -> str:
    if risk >= 60:
        return "High"
    elif risk >= 35:
        return "Medium"
    return "Low"


# ═══════════════════════════════════════════════════════════
# 2. NATURAL LANGUAGE QUERY PROCESSOR (Powered by Groq)
# ═══════════════════════════════════════════════════════════
import httpx
import json

def process_nl_query(query: str, db: Session) -> dict:
    """
    NLP query processor powered by Groq.
    Parses intent from the query, grabs relevant data, and generates a natural language response.
    """
    query_lower = query.lower().strip()
    data = []

    # ── Keep Heuristics to Populate `data` Payload ──
    if any(kw in query_lower for kw in ["low inclusion", "poor inclusion", "worst inclusion"]):
        schools = db.query(School).filter(School.inclusion_score < 50).order_by(
            School.inclusion_score.asc()
        ).limit(10).all()
        data = [
            {"name": s.name, "district": s.district, "state": s.state,
             "inclusion_score": s.inclusion_score}
            for s in schools
        ]
    elif any(kw in query_lower for kw in ["dropout", "drop out", "at risk", "high risk"]):
        students = db.query(Student).filter(Student.dropout_risk >= 60).all()
        data = [
            {"name": s.name, "school_id": s.school_id, "dropout_risk": s.dropout_risk,
             "attendance_rate": s.attendance_rate, "disability_type": s.disability_type}
            for s in students[:15]
        ]
    elif "student" in query_lower:
        # Search for specific students mentioned in the query
        tokens = [w for w in query_lower.split() if len(w) > 3 and w not in ["student", "data", "about", "show", "tell", "what", "is", "the", "score"]]
        found_students = []
        for token in tokens:
            st = db.query(Student).filter(Student.name.ilike(f"%{token}%")).limit(5).all()
            for s in st:
                if s not in found_students:
                    found_students.append(s)
        if found_students:
            data = [
                {"name": s.name, "school_id": s.school_id, "grade_level": s.grade_level,
                 "attendance_rate": s.attendance_rate, "academic_score": s.academic_score,
                 "disability_type": s.disability_type, "socio_economic": s.socio_economic,
                 "dropout_risk": s.dropout_risk}
                for s in found_students[:5]
            ]
    elif any(kw in query_lower for kw in ["ramp", "wheelchair", "accessible"]):
        facilities = db.query(Facility).filter(Facility.has_ramps == False).all()
        school_ids = [f.school_id for f in facilities]
        schools = db.query(School).filter(School.id.in_(school_ids)).all()
        data = [
            {"name": s.name, "district": s.district, "state": s.state,
             "accessibility_score": s.accessibility_score}
            for s in schools[:15]
        ]
    elif any(kw in query_lower for kw in ["rural", "urban", "rural vs", "comparison"]):
        rural = db.query(func.avg(School.inclusion_score)).filter(School.school_type == "Rural").scalar() or 0
        urban = db.query(func.avg(School.inclusion_score)).filter(School.school_type == "Urban").scalar() or 0
        data = [
            {"type": "Rural", "avg_inclusion_score": round(rural, 1)},
            {"type": "Urban", "avg_inclusion_score": round(urban, 1)},
        ]
    elif "state" in query_lower or any(st in query_lower for st in [
        "uttar pradesh", "maharashtra", "tamil nadu", "karnataka",
        "bihar", "rajasthan", "madhya pradesh", "kerala", "west bengal",
    ]):
        states = ["Uttar Pradesh", "Maharashtra", "Tamil Nadu", "Karnataka", "Bihar", "Rajasthan", "Madhya Pradesh", "Kerala", "West Bengal", "Gujarat", "Odisha", "Jharkhand", "Andhra Pradesh", "Telangana"]
        found_state = next((st for st in states if st.lower() in query_lower), None)
        if found_state:
            schools = db.query(School).filter(School.state == found_state).all()
            data = [{"name": s.name, "district": s.district, "inclusion_score": s.inclusion_score, "accessibility_score": s.accessibility_score} for s in schools]
        else:
            from crud import get_dashboard_stats
            stats = get_dashboard_stats(db)
            data = stats["state_wise_inclusion"]
    elif any(kw in query_lower for kw in ["recommend", "suggest", "improve"]):
        schools = db.query(School).filter(School.accessibility_score < 50).order_by(School.accessibility_score.asc()).limit(5).all()
        from models import Facility
        for s in schools:
            facility = db.query(Facility).filter(Facility.school_id == s.id).first()
            rec = {"school": s.name, "district": s.district, "suggestions": []}
            if facility:
                if not facility.has_ramps: rec["suggestions"].append("Install wheelchair ramps")
                if not facility.has_braille_materials: rec["suggestions"].append("Provide braille learning materials")
                if not facility.has_special_educator: rec["suggestions"].append("Hire a trained special educator")
                if not facility.has_accessible_washroom: rec["suggestions"].append("Build accessible washroom facilities")
                if not facility.has_assistive_tech: rec["suggestions"].append("Procure assistive technology devices")
            data.append(rec)

    # ── Generate Answer via Groq ──
    from crud import get_dashboard_stats
    try:
        stats = get_dashboard_stats(db)
        context_stats = {
            "total_schools": stats.get("total_schools"),
            "total_students": stats.get("total_students"),
            "avg_inclusion_score": stats.get("avg_inclusion_score"),
            "avg_accessibility_score": stats.get("avg_accessibility_score"),
            "dropout_risk_high_count": stats.get("dropout_risk_high_count"),
            "avg_attendance": stats.get("avg_attendance")
        }
    except Exception:
        context_stats = "Stats unavailable"

    from dotenv import load_dotenv
    load_dotenv()
    groq_api_key = os.getenv("GROQ_API_KEY")

    if groq_api_key:
        system_prompt = f"""You are the Namaste Inclusive Education AI Assistant. 
You are an expert on this platform which monitors inclusive education across India.
Platform Stats: {json.dumps(context_stats)}
Query Context Data (if relevant records were found in the database): {json.dumps(data) if data else 'None'}
Answer the user's query thoughtfully, accurately, and concisely. Use formatting like bullet points or bold text to make it readable.
Do not talk about being an AI. Just provide the answer based on the provided stats or context data.
If the query is a general question about how the platform works, inclusion scores, or dropout risks, answer based on best practices for inclusive education and logic (e.g., inclusion scores consider facilities, special educators, and attendance; dropout risk considers socioeconomic factors and disability support gaps).
        """
        try:
            response = httpx.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {groq_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.1-8b-instant", 
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": query}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 512
                },
                timeout=10.0
            )
            response.raise_for_status()
            answer = response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[AI Service] Groq API error: {e}")
            answer = f"I'm sorry, I'm having trouble connecting to my brain right now. Please verify your Groq API key is correct. (Error: {e})"
    else:
        answer = "Groq API key is missing. Please set the GROQ_API_KEY environment variable to enable AI responses."

    return {"query": query, "answer": answer, "data": data}

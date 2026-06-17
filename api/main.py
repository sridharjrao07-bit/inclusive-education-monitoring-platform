"""
FastAPI Main Application — Inclusive Education Monitoring Platform

Includes JWT authentication with role-based access control (RBAC).
"""
from fastapi import FastAPI, Depends, HTTPException, Query, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
import os
import sys
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import engine, get_db, Base
from models import School, Facility, Student, Teacher, Feedback, User
from schemas import (
    SchoolOut, SchoolCreate, FacilityBase, FacilityOut, 
    StudentCreate, StudentOut, TeacherCreate, TeacherOut, 
    FeedbackCreate, FeedbackOut, UserCreate, UserOut, Token,
    NLQueryRequest, NLQueryResponse
)
import crud
import ai_service
from adapters.csv_adapter import CSVAdapter
from adapters.json_adapter import JSONAdapter
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    get_optional_user,
    require_admin,
    require_national_admin,
    require_teacher_or_admin,
    require_own_school,
    ADMIN_ROLES,
)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Inclusive Education Platform - India",
    description="Digital platform for monitoring inclusive education programs across India",
    version="1.0.0",
)

# CORS — allow the React frontend (env-configurable for production)
FRONTEND_URL = os.getenv("FRONTEND_URL", "*")
cors_origins = [FRONTEND_URL] if FRONTEND_URL != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def normalize_school_code(code: Optional[str]) -> Optional[str]:
    """Store and compare school codes in one canonical format."""
    if code is None:
        return None
    normalized = code.strip().upper()
    return normalized or None


def normalize_name(value: Optional[str]) -> str:
    return " ".join((value or "").split()).strip()


def school_name_exists(db: Session, name: str) -> bool:
    normalized = normalize_name(name).lower()
    return db.query(School).filter(func.lower(func.trim(School.name)) == normalized).first() is not None


# ═══════════════════════════════════════════════════════════
# STARTUP: Fix PostgreSQL sequence desync (safe no-op on SQLite)
# ═══════════════════════════════════════════════════════════
from sqlalchemy import text as _sql_text

@app.on_event("startup")
def reset_postgres_sequences():
    """Reset auto-increment sequences to MAX(id) for all tables.
    This prevents UniqueViolation errors after bulk data imports."""
    from database import DATABASE_URL
    if not DATABASE_URL.startswith("postgresql"):
        return  # SQLite manages this automatically
    _tables = ["schools", "users", "facilities", "students", "teachers", "feedbacks"]
    try:
        with engine.connect() as conn:
            for tbl in _tables:
                try:
                    row = conn.execute(_sql_text(f"SELECT MAX(id) FROM {tbl}")).scalar() or 0
                    conn.execute(_sql_text(f"SELECT setval('{tbl}_id_seq', {max(row, 1)})"))
                except Exception:
                    pass
            conn.commit()
    except Exception:
        pass  # Non-fatal — server still starts


# ═══════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════
@app.get("/")
def root():
    return {"status": "ok", "message": "Inclusive Education Platform API"}


# ═══════════════════════════════════════════════════════════
# AUTHENTICATION
# ═══════════════════════════════════════════════════════════
@app.post("/auth/register")
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    user_data.username = user_data.username.strip()
    user_data.email = user_data.email.strip().lower()

    # Check if username already exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
        
    # Check if email already exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Validate state_admin must have a state
    if user_data.role == "state_admin" and not user_data.state:
        raise HTTPException(status_code=400, detail="State admins must be assigned a state")
        
    school_id = None
    created_school_code = None
    
    if user_data.role in ("teacher", "student"):
        if user_data.role == "teacher" and user_data.new_school:
            # Create a brand new school
            from models import generate_school_code
            school_name = normalize_name(user_data.new_school.name)
            if not school_name:
                raise HTTPException(status_code=400, detail="School name is required")
            if school_name_exists(db, school_name):
                raise HTTPException(status_code=400, detail="A school with this name is already registered")

            district = normalize_name(user_data.new_school.district)
            state = normalize_name(user_data.new_school.state)
            if not district or not state:
                raise HTTPException(status_code=400, detail="School district and state are required")

            requested_code = normalize_school_code(user_data.new_school.registration_code)
            if requested_code and db.query(School).filter(School.registration_code == requested_code).first():
                raise HTTPException(status_code=400, detail="School registration code is already in use")
            code = requested_code
            for _ in range(10):
                code = code or generate_school_code()
                if not db.query(School).filter(School.registration_code == code).first():
                    break
                code = None
            if not code:
                raise HTTPException(status_code=500, detail="Could not generate a unique school registration code")

            new_school = School(
                name=school_name,
                district=district,
                state=state,
                school_type=user_data.new_school.school_type,
                registration_code=code,
                board="State Board",
                medium="Hindi"
            )
            db.add(new_school)
            db.flush() # Flush to get new_school.id without committing transaction
            
            # Add basic facility for the school
            facility = Facility(school_id=new_school.id)
            db.add(facility)
            db.flush()
            
            school_id = new_school.id
            created_school_code = code
            
        elif user_data.school_code:
            # Join existing school by code (for both teachers and students)
            school_code = normalize_school_code(user_data.school_code)
            school = db.query(School).filter(School.registration_code == school_code).first()
            if not school:
                raise HTTPException(status_code=404, detail="Invalid School Registration Code")
            school_id = school.id
            created_school_code = school.registration_code
            
        else:
            msg = "Students must provide a valid school_code to join a school." if user_data.role == "student" else "Teachers must provide a valid school_code or new_school details."
            raise HTTPException(status_code=400, detail=msg)

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        role=user_data.role,
        school_id=school_id,
        state=user_data.state,
    )
    db.add(new_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Registration could not be completed because of duplicate data")
    db.refresh(new_user)
    
    # We return the UserOut data + optionally the generated school_code if they just created one!
    return {
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "role": new_user.role,
            "school_id": new_user.school_id,
            "state": new_user.state,
            "is_active": new_user.is_active,
        },
        "school_code": created_school_code
    }



@app.get("/auth/verify-code/{code}")
def verify_school_code(code: str, db: Session = Depends(get_db)):
    """Validate a school registration code and return school info."""
    school = db.query(School).filter(School.registration_code == normalize_school_code(code)).first()
    if not school:
        raise HTTPException(status_code=404, detail="Invalid school code")
    return {
        "valid": True,
        "school_name": school.name,
        "district": school.district,
        "state": school.state,
        "school_type": school.school_type,
    }


@app.post("/auth/login", response_model=Token)
async def login(request: Request, db: Session = Depends(get_db)):
    """Authenticate user with form data or JSON and return a JWT token."""
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        payload = await request.json()
        username = (payload.get("username") or "").strip()
        password = payload.get("password") or ""
    else:
        form_data = await request.form()
        username = (form_data.get("username") or "").strip()
        password = form_data.get("password") or ""

    if not username or not password:
        raise HTTPException(
            status_code=400,
            detail="Username and password are required",
        )

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    access_token = create_access_token(data={
        "sub": user.username,
        "role": user.role,
        "state": user.state,
    })
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/auth/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return current_user


@app.post("/auth/seed-admin")
def seed_admin(db: Session = Depends(get_db)):
    """Create default admin users if none exist. Safe to call multiple times."""
    if db.query(User).first():
        return {"message": "Users already exist — skipped."}

    # Ensure there is at least one school for the teacher
    school = db.query(School).first()
    if not school:
        school = School(
            name="Demo School",
            district="Demo District",
            state="Madhya Pradesh",
            school_type="Urban",
            board="CBSE",
            medium="English"
        )
        db.add(school)
        db.commit()
        db.refresh(school)
        
        # Add basic facility for the school
        facility = Facility(school_id=school.id)
        db.add(facility)
        db.commit()

    defaults = [
        {"username": "admin", "email": "admin@edu.gov.in", "password": "admin123",
         "role": "national_admin", "state": None, "school_id": None},
        {"username": "state_mp", "email": "mp@edu.gov.in", "password": "state123",
         "role": "state_admin", "state": "Madhya Pradesh", "school_id": None},
        {"username": "teacher1", "email": "teacher1@school.in", "password": "teacher123",
         "role": "teacher", "state": None, "school_id": school.id},
    ]
    for u in defaults:
        user = User(
            username=u["username"],
            email=u["email"],
            hashed_password=hash_password(u["password"]),
            role=u["role"],
            state=u["state"],
            school_id=u["school_id"],
        )
        db.add(user)
    db.commit()
    return {"message": "Default users created", "users": [d["username"] for d in defaults]}


# ═══════════════════════════════════════════════════════════
# DASHBOARD STATS  (Public read access for demo)
# ═══════════════════════════════════════════════════════════
import time as _time
_stats_cache: dict = {}
_CACHE_TTL = 300  # 5 minutes

@app.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    """Quick connectivity check — does NOT run heavy stats query."""
    from sqlalchemy import text
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/api/stats/summary")
def get_stats_summary(
    state: str = Query(None),
    db: Session = Depends(get_db),
):
    """Fast KPI counts only — returns in <1s."""
    cache_key = f"summary_{state or '__all__'}"
    cached = _stats_cache.get(cache_key)
    if cached and (_time.time() - cached["ts"]) < _CACHE_TTL:
        return cached["data"]
    result = crud.get_dashboard_summary(db, state=state)
    _stats_cache[cache_key] = {"data": result, "ts": _time.time()}
    return result

@app.get("/api/stats")
def get_stats(
    state: str = Query(None),
    db: Session = Depends(get_db),
):
    cache_key = state or "__all__"
    cached = _stats_cache.get(cache_key)
    if cached and (_time.time() - cached["ts"]) < _CACHE_TTL:
        return cached["data"]
    result = crud.get_dashboard_stats(db, state=state)
    _stats_cache[cache_key] = {"data": result, "ts": _time.time()}
    return result


# ═══════════════════════════════════════════════════════════
# SCHOOLS
# ═══════════════════════════════════════════════════════════
@app.get("/api/schools", response_model=list[SchoolOut])
def list_schools(
    skip: int = 0,
    limit: int = 100,
    state: str = Query(None),
    school_type: str = Query(None),
    search: str = Query(None),
    db: Session = Depends(get_db),
):
    return crud.get_schools(db, skip=skip, limit=limit, state=state, school_type=school_type, search=search)


@app.get("/api/schools/{school_id}", response_model=SchoolOut)
def get_school(
    school_id: int,
    db: Session = Depends(get_db),
):
    school = crud.get_school(db, school_id)
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    return school


@app.post("/api/schools", response_model=SchoolOut)
def create_school(
    school: SchoolCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    school.name = normalize_name(school.name)
    school.district = normalize_name(school.district)
    school.state = normalize_name(school.state)
    if not school.name or not school.district or not school.state:
        raise HTTPException(status_code=400, detail="School name, district, and state are required")
    if school_name_exists(db, school.name):
        raise HTTPException(status_code=400, detail="A school with this name is already registered")
    return crud.create_school(db, school)


@app.put("/api/schools/{school_id}/facility")
def update_facility(
    school_id: int,
    facility_data: FacilityBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Admins can update any school; teachers only their own
    if current_user.role == "teacher" and current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="You can only update your own school's facility")

    facility = db.query(Facility).filter(Facility.school_id == school_id).first()
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    for key, value in facility_data.model_dump().items():
        setattr(facility, key, value)
    db.commit()
    crud.recalculate_school_scores(db, school_id)
    return {"status": "updated", "school_id": school_id}


# ═══════════════════════════════════════════════════════════
# ATTENDANCE STATS  (Server-side aggregation for speed)
# ═══════════════════════════════════════════════════════════
@app.get("/api/attendance-stats")
def get_attendance_stats(
    state: str = Query(None),
    db: Session = Depends(get_db),
):
    """Returns pre-aggregated attendance data so the frontend doesn't need to fetch all students."""
    from sqlalchemy import func as sqlfunc, case

    # 1. Per-school aggregation in SQL
    query = (
        db.query(
            Student.school_id,
            sqlfunc.count(Student.id).label("total"),
            sqlfunc.avg(Student.attendance_rate).label("avg_att"),
            sqlfunc.sum(case((Student.attendance_rate < 60, 1), else_=0)).label("low_count"),
            sqlfunc.sum(case((Student.attendance_rate < 40, 1), else_=0)).label("critical_count"),
        )
        .join(School, Student.school_id == School.id)
    )
    if state:
        query = query.filter(School.state == state)
    
    school_agg = query.group_by(Student.school_id).all()

    school_ids = [row.school_id for row in school_agg]
    schools = db.query(School).filter(School.id.in_(school_ids)).all()
    school_map = {s.id: s for s in schools}

    # 2. Fetch only low-attendance students (< 60%) — much smaller than all 5000
    student_query = (
        db.query(Student)
        .join(School, Student.school_id == School.id)
        .filter(Student.attendance_rate < 60)
    )
    if state:
        student_query = student_query.filter(School.state == state)

    low_students = (
        student_query.order_by(Student.attendance_rate.asc())
        .limit(200)
        .all()
    )

    # 3. Build response
    all_total = sum(r.total for r in school_agg)
    all_avg = sum(r.avg_att * r.total for r in school_agg) / all_total if all_total > 0 else 0
    all_low = sum(r.low_count for r in school_agg)
    all_critical = sum(r.critical_count for r in school_agg)
    all_good = all_total - all_low

    school_stats = []
    for row in school_agg:
        s = school_map.get(row.school_id)
        if not s:
            continue
        school_stats.append({
            "id": s.id,
            "name": s.name,
            "district": s.district,
            "state": s.state,
            "school_type": s.school_type,
            "avg_attendance": round(row.avg_att, 1),
            "total_students": row.total,
            "low_count": row.low_count,
            "critical_count": row.critical_count,
        })
    school_stats.sort(key=lambda x: x["avg_attendance"])

    student_list = [
        {
            "id": st.id, "name": st.name, "school_id": st.school_id,
            "gender": st.gender, "category": st.category,
            "grade_level": st.grade_level,
            "attendance_rate": st.attendance_rate,
            "dropout_risk": st.dropout_risk,
        }
        for st in low_students
    ]

    return {
        "summary": {
            "total_students": all_total,
            "avg_attendance": round(all_avg, 1),
            "good_count": all_good,
            "low_count": all_low,
            "critical_count": all_critical,
        },
        "school_stats": school_stats,
        "low_students": student_list,
    }


# ═══════════════════════════════════════════════════════════
# STUDENTS
# ═══════════════════════════════════════════════════════════
@app.get("/api/students", response_model=list[StudentOut])
def list_students(
    school_id: int = Query(None),
    skip: int = 0,
    limit: int = 200,
    db: Session = Depends(get_db),
):
    return crud.get_students(db, school_id=school_id, skip=skip, limit=limit)


@app.post("/api/students", response_model=StudentOut)
def create_student(
    student: StudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Teachers can only add students to their own school
    if current_user.role == "teacher" and current_user.school_id != student.school_id:
        raise HTTPException(status_code=403, detail="You can only add students to your own school")
    result = crud.create_student(db, student)
    crud.recalculate_school_scores(db, student.school_id)
    return result


# ═══════════════════════════════════════════════════════════
# TEACHERS
# ═══════════════════════════════════════════════════════════
@app.get("/api/teachers", response_model=list[TeacherOut])
def list_teachers(
    school_id: int = Query(None),
    db: Session = Depends(get_db),
):
    return crud.get_teachers(db, school_id=school_id)


@app.post("/api/teachers", response_model=TeacherOut)
def create_teacher(
    teacher: TeacherCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return crud.create_teacher(db, teacher)


# ═══════════════════════════════════════════════════════════
# FEEDBACK
# ═══════════════════════════════════════════════════════════
@app.get("/api/feedbacks", response_model=list[FeedbackOut])
def list_feedbacks(
    school_id: int = Query(None),
    db: Session = Depends(get_db),
):
    return crud.get_feedbacks(db, school_id=school_id)


@app.post("/api/feedbacks", response_model=FeedbackOut)
def create_feedback(
    feedback: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.create_feedback(db, feedback)


# ═══════════════════════════════════════════════════════════
# AI / NLP QUERY
# ═══════════════════════════════════════════════════════════
@app.post("/api/query", response_model=NLQueryResponse)
def nl_query(
    req: NLQueryRequest,
    db: Session = Depends(get_db),
):
    result = ai_service.process_nl_query(req.query, db)
    return result


# ═══════════════════════════════════════════════════════════
# AI / DROPOUT RISK FOR A SPECIFIC STUDENT
# ═══════════════════════════════════════════════════════════
@app.get("/api/students/{student_id}/risk")
def get_student_risk(
    student_id: int,
    db: Session = Depends(get_db),
):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return {
        "student_id": student.id,
        "name": student.name,
        "dropout_risk": student.dropout_risk,
        "risk_label": ai_service.get_risk_label(student.dropout_risk),
        "model_type": "ml" if ai_service.ml_model else "heuristic",
        "factors": {
            "attendance_rate": student.attendance_rate,
            "academic_score": student.academic_score,
            "disability_type": student.disability_type,
        },
    }


# ═══════════════════════════════════════════════════════════
# DATA INGESTION (ADAPTER PATTERN)
# ═══════════════════════════════════════════════════════════
def _process_ingestion(records: list, db: Session):
    """Common logic for inserting parsed records into DB."""
    schools_created = 0
    students_created = 0
    
    # Simple pass: create schools first
    school_map = {}  # (name, state) -> school_id
    
    for r in records:
        if r.get("_type") in ("school", "mixed"):
            key = (r["school_name"], r["state"])
            if key not in school_map:
                # Check if exists in DB
                existing = db.query(School).filter(
                    School.name == r["school_name"], 
                    School.state == r["state"]
                ).first()
                if existing:
                    school_map[key] = existing.id
                else:
                    # Create new
                    school = School(
                        name=r["school_name"],
                        district=r["district"],
                        state=r["state"],
                        school_type=r["school_type"],
                        board=r.get("board", "State Board"),
                        medium=r.get("medium", "Hindi")
                    )
                    db.add(school)
                    db.commit()
                    db.refresh(school)
                    school_map[key] = school.id
                    schools_created += 1
                    
                    # Create facility
                    facility = Facility(
                        school_id=school.id,
                        has_ramps=r.get("has_ramps", False),
                        has_braille_materials=r.get("has_braille_materials", False),
                        has_assistive_tech=r.get("has_assistive_tech", False),
                        has_special_educator=r.get("has_special_educator", False),
                        has_accessible_washroom=r.get("has_accessible_washroom", False),
                        has_transport=r.get("has_transport", False),
                        has_computer_lab=r.get("has_computer_lab", False),
                        has_library=r.get("has_library", False),
                    )
                    db.add(facility)
                    db.commit()

    # Second pass: create students
    for r in records:
        if r.get("_type") in ("student", "mixed") and r.get("student_name"):
            # find school_id
            if "_school_ref" in r:
                # Nested JSON passed a reference index
                # This is a bit brittle, fallback to school name if needed
                # For simplicity, if school_name is present, use that:
                key = (r.get("school_name", ""), r.get("state", ""))
            else:
                key = (r["school_name"], r["state"])
            
            school_id = school_map.get(key)
            if school_id:
                # Basic heuristic calculation
                school = db.query(School).filter(School.id == school_id).first()
                facility = db.query(Facility).filter(Facility.school_id == school_id).first()
                
                risk = ai_service.predict_dropout_risk(
                    attendance_rate=r.get("attendance_rate", 75.0),
                    academic_score=r.get("academic_score", 50.0),
                    disability_type=r.get("disability_type", "None"),
                    socio_economic=r.get("socio_economic", "Middle"),
                    school_type=school.school_type if school else "Urban",
                    has_ramps=facility.has_ramps if facility else False,
                    has_assistive_tech=facility.has_assistive_tech if facility else False,
                    has_special_educator=facility.has_special_educator if facility else False,
                )
                
                student = Student(
                    school_id=school_id,
                    name=r["student_name"],
                    gender=r.get("gender", "Other"),
                    category=r.get("category", "General"),
                    disability_type=r.get("disability_type", "None"),
                    socio_economic=r.get("socio_economic", "Middle"),
                    enrollment_status=r.get("enrollment_status", "Active"),
                    attendance_rate=r.get("attendance_rate", 75.0),
                    grade_level=r.get("grade_level", 1),
                    academic_score=r.get("academic_score", 50.0),
                    dropout_risk=risk
                )
                db.add(student)
                students_created += 1

    db.commit()
    
    # Recalculate scores for all touched schools
    for sid in school_map.values():
        crud.recalculate_school_scores(db, sid)
        
    return {"schools_created": schools_created, "students_created": students_created}


@app.post("/api/ingest/csv")
async def ingest_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_national_admin)
):
    """Admin-only: Bulk upload CSV using CSVAdapter."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Must be a CSV file")
        
    content = await file.read()
    adapter = CSVAdapter()
    raw_records = adapter.parse(content, file.filename)
    valid_records, errors = adapter.validate(raw_records)
    
    if not valid_records and errors:
        raise HTTPException(status_code=400, detail={"errors": errors[:10]})
        
    stats = _process_ingestion(valid_records, db)
    return {
        "status": "success",
        "rows_processed": len(raw_records),
        "valid_records": len(valid_records),
        "errors": errors[:10],  # Return max 10 errors
        "inserted": stats
    }


@app.post("/api/ingest/json")
async def ingest_json(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_national_admin)
):
    """Admin-only: Bulk upload JSON using JSONAdapter."""
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Must be a JSON file")
        
    content = await file.read()
    adapter = JSONAdapter()
    
    try:
        raw_records = adapter.parse(content, file.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON format: {str(e)}")
        
    valid_records, errors = adapter.validate(raw_records)
    
    if not valid_records and errors:
        raise HTTPException(status_code=400, detail={"errors": errors[:10]})
        
    stats = _process_ingestion(valid_records, db)
    return {
        "status": "success",
        "rows_processed": len(raw_records),
        "valid_records": len(valid_records),
        "errors": errors[:10],
        "inserted": stats
    }

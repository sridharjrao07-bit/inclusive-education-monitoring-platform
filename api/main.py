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
import schemas
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

    # ── Security: Block privileged role self-registration ──────────────────
    # national_admin, state_admin, and the legacy "admin" role MUST be created
    # directly by an existing admin (e.g. via the seed endpoint or a future
    # admin-only management API). They cannot be self-registered via this endpoint.
    PRIVILEGED_ROLES = ("national_admin", "state_admin", "admin")
    if user_data.role in PRIVILEGED_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Privileged roles (national_admin, state_admin) cannot be self-registered. "
                   "Please contact your system administrator to have your account created.",
        )

    # Validate state_admin must have a state (kept for any future admin-creation flow)
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
# ADMIN USER MANAGEMENT  (national_admin only)
# ═══════════════════════════════════════════════════════════
class AdminUserCreate(schemas.BaseModel if hasattr(schemas, 'BaseModel') else object):
    pass

from pydantic import BaseModel as _PydanticBase, EmailStr as _EmailStr

class AdminCreateUserRequest(_PydanticBase):
    username: str
    email: str
    password: str
    role: str          # "national_admin" | "state_admin" | "teacher"
    state: Optional[str] = None   # Required for state_admin

class AdminUserOut(_PydanticBase):
    id: int
    username: str
    email: str
    role: str
    state: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


@app.post("/auth/admin/create-user", response_model=AdminUserOut)
def admin_create_user(
    body: AdminCreateUserRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_national_admin),
):
    """
    National Admin only — create a new user of any role.
    This is the proper way to provision national_admin / state_admin accounts
    without exposing the operation to the public registration form.
    """
    ALLOWED_ROLES = ("national_admin", "state_admin", "teacher")
    if body.role not in ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {ALLOWED_ROLES}")

    if body.role == "state_admin" and not body.state:
        raise HTTPException(status_code=400, detail="State admins must be assigned a state")

    body.username = body.username.strip()
    body.email = body.email.strip().lower()

    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
        role=body.role,
        state=body.state,
        school_id=None,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.get("/auth/admin/users", response_model=list[AdminUserOut])
def admin_list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_national_admin),
):
    """National Admin only — list all registered users."""
    return db.query(User).order_by(User.created_at.desc()).all()


@app.patch("/auth/admin/users/{user_id}/toggle-active")
def admin_toggle_user_active(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_national_admin),
):
    """National Admin only — activate or deactivate a user account."""
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot deactivate your own account")
    target.is_active = not target.is_active
    db.commit()
    return {"id": target.id, "username": target.username, "is_active": target.is_active}


@app.delete("/auth/admin/users/{user_id}")
def admin_delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_national_admin),
):
    """National Admin only — permanently delete a user account."""
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")
    username = target.username
    db.delete(target)
    db.commit()
    return {"deleted": True, "username": username}



# ═══════════════════════════════════════════════════════════
# STATE ADMIN USER MANAGEMENT  (state_admin only, scoped to their state)
# ═══════════════════════════════════════════════════════════
from auth import require_admin as _require_admin  # already imported, no-op

from pydantic import BaseModel as _SA_Base

class StateAdminCreateTeacherRequest(_SA_Base):
    username: str
    email: str
    password: str
    school_code: Optional[str] = None   # must be a school in their state


@app.post("/auth/state-admin/create-teacher")
def state_admin_create_teacher(
    body: StateAdminCreateTeacherRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    State Admin only — create a teacher account for a school in their state.
    Optionally links the teacher to an existing school via school_code.
    """
    if current_user.role not in ("state_admin", "national_admin", "admin"):
        raise HTTPException(status_code=403, detail="State admin access required")

    body.username = body.username.strip()
    body.email = body.email.strip().lower()

    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    school_id = None
    if body.school_code:
        school_code = normalize_school_code(body.school_code)
        school = db.query(School).filter(School.registration_code == school_code).first()
        if not school:
            raise HTTPException(status_code=404, detail="Invalid school code")
        # State admins can only assign to schools in their own state
        if current_user.role == "state_admin" and school.state != current_user.state:
            raise HTTPException(
                status_code=403,
                detail=f"School is not in your state ({current_user.state})"
            )
        school_id = school.id

    new_user = User(
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
        role="teacher",
        state=current_user.state if current_user.role == "state_admin" else None,
        school_id=school_id,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email,
        "role": new_user.role,
        "state": new_user.state,
        "school_id": new_user.school_id,
        "is_active": new_user.is_active,
    }


@app.get("/auth/state-admin/users")
def state_admin_list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """State Admin only — list teachers/users within their state.
    national_admin accounts are NEVER returned regardless of caller role.
    """
    if current_user.role not in ("state_admin", "national_admin", "admin"):
        raise HTTPException(status_code=403, detail="State admin access required")

    # ── Always exclude national_admin rows from this view ────────────────
    query = db.query(User).filter(User.role != "national_admin")

    if current_user.role == "state_admin":
        state_school_ids = [
            s.id for s in db.query(School).filter(School.state == current_user.state).all()
        ]
        query = query.filter(
            (User.school_id.in_(state_school_ids)) |
            (User.state == current_user.state)
        )

    users = query.order_by(User.created_at.desc()).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "state": u.state,
            "school_id": u.school_id,
            "is_active": u.is_active,
        }
        for u in users
    ]


@app.patch("/auth/state-admin/users/{user_id}/toggle-active")
def state_admin_toggle_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """State Admin only — enable/disable a teacher account in their state."""
    if current_user.role not in ("state_admin", "national_admin", "admin"):
        raise HTTPException(status_code=403, detail="State admin access required")

    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot deactivate your own account")

    # ── Hard block: national_admin is ALWAYS off-limits, regardless of caller ──
    if target.role == "national_admin":
        raise HTTPException(
            status_code=403,
            detail="National admin accounts cannot be managed through this endpoint"
        )

    # ── State admin: additional scoping restrictions ────────────────────────
    if current_user.role == "state_admin":
        # Cannot act on another state_admin (same level)
        if target.role == "state_admin":
            raise HTTPException(
                status_code=403,
                detail="State admins cannot manage other state admin accounts"
            )
        # Must be in the same state
        school = db.query(School).filter(School.id == target.school_id).first()
        if school and school.state != current_user.state:
            raise HTTPException(
                status_code=403,
                detail="This user is not associated with a school in your state"
            )
        if target.state and target.state != current_user.state:
            raise HTTPException(
                status_code=403,
                detail="This user belongs to a different state"
            )

    target.is_active = not target.is_active
    db.commit()
    return {"id": target.id, "username": target.username, "is_active": target.is_active}


@app.delete("/auth/state-admin/users/{user_id}")
def state_admin_delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """State Admin only — permanently delete a teacher in their state.

    Security layers (applied in order, no bypass possible):
      1. Caller must be state_admin / national_admin
      2. Target national_admin → ALWAYS blocked (even for national_admin callers on this endpoint)
      3. Target state_admin → blocked for state_admin callers
      4. State boundary → target school must be in caller's state
      5. State field check → target.state must match caller's state
    """
    if current_user.role not in ("state_admin", "national_admin", "admin"):
        raise HTTPException(status_code=403, detail="State admin access required")

    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")

    # ── Layer 1: national_admin is ALWAYS protected on this endpoint ──
    if target.role == "national_admin":
        raise HTTPException(
            status_code=403,
            detail="National admin accounts can only be removed directly from the database"
        )

    # ── Layer 2–4: state_admin caller restrictions ─────────────────────
    if current_user.role == "state_admin":
        # Cannot delete other state_admins
        if target.role == "state_admin":
            raise HTTPException(
                status_code=403,
                detail="State admins cannot delete other state admin accounts"
            )
        # State boundary check via school
        school = db.query(School).filter(School.id == target.school_id).first()
        if school and school.state != current_user.state:
            raise HTTPException(
                status_code=403,
                detail=f"This user belongs to a school in '{school.state}', not '{current_user.state}'"
            )
        # State boundary check via user.state field
        if target.state and target.state != current_user.state:
            raise HTTPException(
                status_code=403,
                detail=f"This user is assigned to '{target.state}', not '{current_user.state}'"
            )

    username = target.username
    db.delete(target)
    db.commit()
    return {"deleted": True, "username": username}


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
    
    if result.dropout_risk >= 60:
        crud.create_notification(
            db=db,
            message=f"High dropout risk ({result.dropout_risk:.1f}%) detected for newly added student {result.name} in grade {result.grade_level}.",
            school_id=result.school_id,
            notification_type="alert"
        )
    
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
# NOTIFICATIONS
# ═══════════════════════════════════════════════════════════
@app.get("/api/notifications", response_model=list[schemas.NotificationOut])
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.get_user_notifications(db, current_user)

@app.post("/api/notifications/{notification_id}/read", response_model=schemas.NotificationOut)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notif = crud.mark_notification_read(db, notification_id)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notif


# ═══════════════════════════════════════════════════════════
# REPORTS (PDF)
# ═══════════════════════════════════════════════════════════
from fastapi.responses import Response
import io
from fpdf import FPDF

@app.get("/api/reports/schools")
def export_schools_report(
    state: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    schools = crud.get_schools(db, limit=1000, state=state)
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=16)
    pdf.cell(200, 10, txt="Schools Report", ln=1, align="C")
    
    pdf.set_font("Helvetica", size=10)
    pdf.ln(10)
    
    # Table Header
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(50, 10, "Name", border=1, fill=True)
    pdf.cell(40, 10, "District", border=1, fill=True)
    pdf.cell(40, 10, "State", border=1, fill=True)
    pdf.cell(30, 10, "Students", border=1, fill=True)
    pdf.cell(30, 10, "Inc. Score", border=1, fill=True)
    pdf.ln()
    
    for s in schools:
        pdf.cell(50, 10, s.name[:25], border=1)
        pdf.cell(40, 10, s.district[:20], border=1)
        pdf.cell(40, 10, s.state[:20], border=1)
        pdf.cell(30, 10, str(s.total_students), border=1)
        pdf.cell(30, 10, f"{s.inclusion_score:.1f}", border=1)
        pdf.ln()

    pdf_bytes = pdf.output()
    return Response(content=bytes(pdf_bytes), media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=schools_report.pdf"})

@app.get("/api/reports/students")
def export_students_report(
    school_id: int = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    # If teacher, enforce their own school
    if current_user.role == "teacher":
        if school_id and school_id != current_user.school_id:
            raise HTTPException(status_code=403, detail="You can only export your own school's data")
        school_id = current_user.school_id

    students = crud.get_students(db, school_id=school_id, limit=5000)
    
    pdf = FPDF(orientation='L') # Landscape for more columns
    pdf.add_page()
    pdf.set_font("Helvetica", size=16)
    pdf.cell(0, 10, txt="Students Report", ln=1, align="C")
    
    pdf.set_font("Helvetica", size=10)
    pdf.ln(10)
    
    # Table Header
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(50, 10, "Name", border=1, fill=True)
    pdf.cell(30, 10, "Gender", border=1, fill=True)
    pdf.cell(40, 10, "Category", border=1, fill=True)
    pdf.cell(40, 10, "Disability", border=1, fill=True)
    pdf.cell(30, 10, "Attendance", border=1, fill=True)
    pdf.cell(30, 10, "Academic", border=1, fill=True)
    pdf.cell(30, 10, "Risk Score", border=1, fill=True)
    pdf.ln()
    
    for st in students:
        pdf.cell(50, 10, st.name[:25], border=1)
        pdf.cell(30, 10, st.gender, border=1)
        pdf.cell(40, 10, st.category, border=1)
        pdf.cell(40, 10, st.disability_type[:20], border=1)
        pdf.cell(30, 10, f"{st.attendance_rate:.1f}%", border=1)
        pdf.cell(30, 10, f"{st.academic_score:.1f}", border=1)
        
        # Highlight high risk
        if st.dropout_risk >= 60:
            pdf.set_text_color(255, 0, 0)
        pdf.cell(30, 10, f"{st.dropout_risk:.1f}", border=1)
        pdf.set_text_color(0, 0, 0) # reset
        
        pdf.ln()

    pdf_bytes = pdf.output()
    return Response(content=bytes(pdf_bytes), media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=students_report.pdf"})

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

                # Generate notification if high risk
                if risk >= 60:
                    crud.create_notification(
                        db=db,
                        message=f"High dropout risk ({risk:.1f}%) detected for student {r['student_name']} in grade {r.get('grade_level', 1)}.",
                        school_id=school_id,
                        notification_type="alert"
                    )

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

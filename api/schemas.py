from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ─── School ──────────────────────────────────────────────
class FacilityBase(BaseModel):
    has_ramps: bool = False
    has_braille_materials: bool = False
    has_assistive_tech: bool = False
    has_special_educator: bool = False
    has_accessible_washroom: bool = False
    has_transport: bool = False
    has_computer_lab: bool = False
    has_library: bool = False


class FacilityOut(FacilityBase):
    id: int
    school_id: int

    class Config:
        from_attributes = True


class SchoolBase(BaseModel):
    name: str
    district: str
    state: str
    school_type: str = "Urban"
    board: str = "State Board"
    medium: str = "Hindi"


class SchoolCreate(SchoolBase):
    pass


class SchoolOut(SchoolBase):
    id: int
    total_students: int
    inclusion_score: float
    accessibility_score: float
    registration_code: str
    facility: Optional[FacilityOut] = None

    class Config:
        from_attributes = True


# ─── Student ─────────────────────────────────────────────
class StudentCreate(BaseModel):
    school_id: int
    name: str
    gender: str
    category: str = "General"
    disability_type: str = "None"
    socio_economic: str = "Middle"
    enrollment_status: str = "Active"
    attendance_rate: float = 85.0
    grade_level: int = 1
    academic_score: float = 50.0


class StudentOut(BaseModel):
    id: int
    school_id: int
    name: str
    gender: str
    category: str
    disability_type: str
    socio_economic: str
    enrollment_status: str
    attendance_rate: float
    grade_level: int
    academic_score: float
    dropout_risk: float

    class Config:
        from_attributes = True


# ─── Teacher ─────────────────────────────────────────────
class TeacherCreate(BaseModel):
    school_id: int
    name: str
    subject: str = "General"
    trained_in_special_ed: bool = False
    years_experience: int = 0


class TeacherOut(BaseModel):
    id: int
    school_id: int
    name: str
    subject: str
    trained_in_special_ed: bool
    years_experience: int

    class Config:
        from_attributes = True


# ─── Feedback ────────────────────────────────────────────
class FeedbackCreate(BaseModel):
    school_id: int
    user_role: str
    rating: int = 3
    comments: str = ""


class FeedbackOut(BaseModel):
    id: int
    school_id: int
    user_role: str
    rating: int
    comments: str

    class Config:
        from_attributes = True


# ─── Dashboard / Stats ───────────────────────────────────
class DashboardStats(BaseModel):
    total_schools: int
    total_students: int
    avg_inclusion_score: float
    avg_accessibility_score: float
    dropout_risk_high_count: int
    avg_attendance: float
    gender_distribution: dict
    category_distribution: dict
    disability_distribution: dict
    school_type_distribution: dict
    state_wise_inclusion: List[dict]
    top_risk_schools: List[dict]


class NLQueryRequest(BaseModel):
    query: str


class NLQueryResponse(BaseModel):
    query: str
    answer: str
    data: Optional[List[dict]] = None


class NewSchoolData(BaseModel):
    name: str
    district: str
    state: str
    school_type: str = "Urban"
    registration_code: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str = "teacher"           # "national_admin" | "state_admin" | "teacher"
    school_code: Optional[str] = None       # To join existing
    new_school: Optional[NewSchoolData] = None # To create new
    state: Optional[str] = None      # Required for state_admin


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: str
    school_id: Optional[int] = None
    state: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str

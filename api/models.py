from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from database import Base
import datetime
import secrets
import string

def generate_school_code():
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))

class School(Base):
    __tablename__ = "schools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    district = Column(String, nullable=False)
    state = Column(String, nullable=False)
    school_type = Column(String, nullable=False)          # Rural / Urban
    board = Column(String, default="State Board")          # CBSE / State Board / ICSE
    medium = Column(String, default="Hindi")
    total_students = Column(Integer, default=0)
    inclusion_score = Column(Float, default=0.0)           # 0-100
    accessibility_score = Column(Float, default=0.0)       # 0-100
    registration_code = Column(String, unique=True, index=True, default=generate_school_code)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    facility = relationship("Facility", back_populates="school", uselist=False)
    students = relationship("Student", back_populates="school")
    teachers = relationship("Teacher", back_populates="school")
    feedbacks = relationship("Feedback", back_populates="school")


class Facility(Base):
    __tablename__ = "facilities"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), unique=True)
    has_ramps = Column(Boolean, default=False)
    has_braille_materials = Column(Boolean, default=False)
    has_assistive_tech = Column(Boolean, default=False)
    has_special_educator = Column(Boolean, default=False)
    has_accessible_washroom = Column(Boolean, default=False)
    has_transport = Column(Boolean, default=False)
    has_computer_lab = Column(Boolean, default=False)
    has_library = Column(Boolean, default=False)

    school = relationship("School", back_populates="facility")


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"))
    name = Column(String, nullable=False)
    gender = Column(String, nullable=False)                # Male / Female / Other
    category = Column(String, default="General")           # General / SC / ST / OBC
    disability_type = Column(String, default="None")       # None / Visual / Hearing / Locomotor / Cognitive / Multiple
    socio_economic = Column(String, default="Middle")      # BPL / Lower / Middle / Upper
    enrollment_status = Column(String, default="Active")   # Active / Dropout / Transferred
    attendance_rate = Column(Float, default=0.0)           # 0-100 percentage
    grade_level = Column(Integer, default=1)               # 1 - 12
    academic_score = Column(Float, default=0.0)            # 0-100
    dropout_risk = Column(Float, default=0.0)              # 0-100 predicted risk
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    school = relationship("School", back_populates="students")


class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"))
    name = Column(String, nullable=False)
    subject = Column(String, default="General")
    trained_in_special_ed = Column(Boolean, default=False)
    years_experience = Column(Integer, default=0)

    school = relationship("School", back_populates="teachers")


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"))
    user_role = Column(String, nullable=False)             # Parent / Student / Teacher
    rating = Column(Integer, default=3)                    # 1-5
    comments = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    school = relationship("School", back_populates="feedbacks")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="teacher")   # "national_admin" | "state_admin" | "teacher"
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True)  # NULL for admins
    state = Column(String, nullable=True)  # For state_admin: filters data to this state
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    school = relationship("School")

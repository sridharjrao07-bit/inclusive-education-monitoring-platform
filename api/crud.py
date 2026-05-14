from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, case, text
from models import School, Facility, Student, Teacher, Feedback
from schemas import SchoolCreate, StudentCreate, TeacherCreate, FeedbackCreate


# ─── School CRUD ─────────────────────────────────────────
def get_schools(db: Session, skip: int = 0, limit: int = 100,
                state: str = None, school_type: str = None):
    q = db.query(School).options(joinedload(School.facility))
    if state:
        q = q.filter(School.state == state)
    if school_type:
        q = q.filter(School.school_type == school_type)
    return q.offset(skip).limit(limit).all()


def get_school(db: Session, school_id: int):
    return db.query(School).filter(School.id == school_id).first()


def create_school(db: Session, school: SchoolCreate):
    db_school = School(**school.model_dump())
    db.add(db_school)
    db.commit()
    db.refresh(db_school)

    # Create empty facility record
    facility = Facility(school_id=db_school.id)
    db.add(facility)
    db.commit()
    return db_school


# ─── Student CRUD ────────────────────────────────────────
def get_students(db: Session, school_id: int = None, skip: int = 0, limit: int = 200):
    q = db.query(Student)
    if school_id:
        q = q.filter(Student.school_id == school_id)
    return q.offset(skip).limit(limit).all()


def create_student(db: Session, student: StudentCreate):
    from ai_service import predict_dropout_risk
    db_student = Student(**student.model_dump())

    # Get the school's facility for risk calculation
    facility = db.query(Facility).filter(Facility.school_id == student.school_id).first()
    school = db.query(School).filter(School.id == student.school_id).first()

    db_student.dropout_risk = predict_dropout_risk(
        attendance_rate=student.attendance_rate,
        academic_score=student.academic_score,
        disability_type=student.disability_type,
        socio_economic=student.socio_economic,
        school_type=school.school_type if school else "Urban",
        has_ramps=facility.has_ramps if facility else False,
        has_assistive_tech=facility.has_assistive_tech if facility else False,
        has_special_educator=facility.has_special_educator if facility else False,
    )

    db.add(db_student)
    db.commit()
    db.refresh(db_student)

    # Update school student count
    if school:
        school.total_students = db.query(Student).filter(
            Student.school_id == school.id
        ).count()
        db.commit()

    return db_student


# ─── Teacher CRUD ────────────────────────────────────────
def get_teachers(db: Session, school_id: int = None, limit: int = 500):
    q = db.query(Teacher)
    if school_id:
        q = q.filter(Teacher.school_id == school_id)
    return q.limit(limit).all()


def create_teacher(db: Session, teacher: TeacherCreate):
    db_teacher = Teacher(**teacher.model_dump())
    db.add(db_teacher)
    db.commit()
    db.refresh(db_teacher)
    return db_teacher


# ─── Feedback CRUD ───────────────────────────────────────
def get_feedbacks(db: Session, school_id: int = None):
    q = db.query(Feedback)
    if school_id:
        q = q.filter(Feedback.school_id == school_id)
    return q.all()


def create_feedback(db: Session, feedback: FeedbackCreate):
    db_fb = Feedback(**feedback.model_dump())
    db.add(db_fb)
    db.commit()
    db.refresh(db_fb)
    return db_fb


# ─── Score Calculations ──────────────────────────────────
def calculate_accessibility_score(facility: Facility) -> float:
    if not facility:
        return 0.0
    features = [
        facility.has_ramps,
        facility.has_braille_materials,
        facility.has_assistive_tech,
        facility.has_special_educator,
        facility.has_accessible_washroom,
        facility.has_transport,
        facility.has_computer_lab,
        facility.has_library,
    ]
    return round((sum(features) / len(features)) * 100, 1)


def calculate_inclusion_score(db: Session, school_id: int) -> float:
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        return 0.0

    # Component 1: Accessibility (40%)
    acc_score = school.accessibility_score

    # Component 2: Diversity (30%) — ratio of non-General + disabled students
    total = db.query(Student).filter(Student.school_id == school_id).count()
    if total == 0:
        return acc_score * 0.4

    diverse = db.query(Student).filter(
        Student.school_id == school_id,
        (Student.category != "General") | (Student.disability_type != "None")
    ).count()
    diversity_score = min((diverse / total) * 200, 100)  # normalized

    # Component 3: Attendance (20%)
    avg_att = db.query(func.avg(Student.attendance_rate)).filter(
        Student.school_id == school_id
    ).scalar() or 0

    # Component 4: Teacher training (10%)
    total_teachers = db.query(Teacher).filter(Teacher.school_id == school_id).count()
    trained = db.query(Teacher).filter(
        Teacher.school_id == school_id,
        Teacher.trained_in_special_ed == True
    ).count()
    teacher_score = (trained / total_teachers * 100) if total_teachers > 0 else 0

    score = (acc_score * 0.4) + (diversity_score * 0.3) + (avg_att * 0.2) + (teacher_score * 0.1)
    return round(score, 1)


def recalculate_school_scores(db: Session, school_id: int):
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        return

    facility = db.query(Facility).filter(Facility.school_id == school_id).first()
    school.accessibility_score = calculate_accessibility_score(facility)
    school.inclusion_score = calculate_inclusion_score(db, school_id)
    school.total_students = db.query(Student).filter(Student.school_id == school_id).count()
    db.commit()


# ─── Dashboard Stats ─────────────────────────────────────────
def get_dashboard_summary(db: Session, state: str = None):
    """Fast summary: only school + student aggregate counts. Returns in <500ms."""
    school_filter = School.state == state if state else True

    school_agg = db.query(
        func.count(School.id).label("total_schools"),
        func.avg(School.inclusion_score).label("avg_inclusion"),
        func.avg(School.accessibility_score).label("avg_accessibility"),
    ).filter(school_filter).one()

    student_school_subq = (
        db.query(School.id).filter(school_filter).subquery()
    ) if state else None

    student_q = db.query(Student)
    if state:
        student_q = student_q.filter(Student.school_id.in_(student_school_subq))

    student_agg = student_q.with_entities(
        func.count(Student.id).label("total_students"),
        func.avg(Student.attendance_rate).label("avg_attendance"),
        func.sum(case((Student.dropout_risk >= 60, 1), else_=0)).label("high_risk"),
    ).one()

    return {
        "total_schools": school_agg.total_schools or 0,
        "total_students": student_agg.total_students or 0,
        "avg_inclusion_score": round(school_agg.avg_inclusion or 0, 1),
        "avg_accessibility_score": round(school_agg.avg_accessibility or 0, 1),
        "dropout_risk_high_count": int(student_agg.high_risk or 0),
        "avg_attendance": round(float(student_agg.avg_attendance or 0), 1),
        # Empty placeholders - charts endpoint fills these
        "gender_distribution": {},
        "category_distribution": {},
        "disability_distribution": {},
        "school_type_distribution": {},
        "state_wise_inclusion": [],
        "top_risk_schools": [],
    }


def get_dashboard_stats(db: Session, state: str = None):
    """Fast dashboard stats using SQL-level conditional aggregation."""

    # ── Base filters ──────────────────────────────────────
    school_filter = School.state == state if state else True
    student_school_subq = (
        db.query(School.id)
        .filter(school_filter)
        .subquery()
    ) if state else None

    # ── School-level aggregates ───────────────────────────
    school_agg = db.query(
        func.count(School.id).label("total_schools"),
        func.avg(School.inclusion_score).label("avg_inclusion"),
        func.avg(School.accessibility_score).label("avg_accessibility"),
    ).filter(school_filter).one()

    # ── Single-pass Student aggregates ────────────────────
    student_q = db.query(Student)
    if state:
        student_q = student_q.filter(Student.school_id.in_(student_school_subq))

    student_agg = student_q.with_entities(
        func.count(Student.id).label("total_students"),
        func.avg(Student.attendance_rate).label("avg_attendance"),
        func.sum(case((Student.dropout_risk >= 60, 1), else_=0)).label("high_risk"),
        
        func.sum(case((Student.gender == 'Male', 1), else_=0)).label("g_male"),
        func.sum(case((Student.gender == 'Female', 1), else_=0)).label("g_female"),
        func.sum(case((Student.gender == 'Other', 1), else_=0)).label("g_other"),
        
        func.sum(case((Student.category == 'General', 1), else_=0)).label("c_general"),
        func.sum(case((Student.category == 'OBC', 1), else_=0)).label("c_obc"),
        func.sum(case((Student.category == 'SC', 1), else_=0)).label("c_sc"),
        func.sum(case((Student.category == 'ST', 1), else_=0)).label("c_st"),
        
        func.sum(case((Student.disability_type == 'None', 1), else_=0)).label("d_none"),
        func.sum(case((Student.disability_type == 'Visual', 1), else_=0)).label("d_visual"),
        func.sum(case((Student.disability_type == 'Hearing', 1), else_=0)).label("d_hearing"),
        func.sum(case((Student.disability_type == 'Locomotor', 1), else_=0)).label("d_locomotor"),
        func.sum(case((Student.disability_type == 'Cognitive', 1), else_=0)).label("d_cognitive"),
        func.sum(case((Student.disability_type == 'Multiple', 1), else_=0)).label("d_multiple"),
    ).one()

    gender_dist = {
        "Male": int(student_agg.g_male or 0),
        "Female": int(student_agg.g_female or 0),
        "Other": int(student_agg.g_other or 0)
    }
    
    cat_dist = {
        "General": int(student_agg.c_general or 0),
        "OBC": int(student_agg.c_obc or 0),
        "SC": int(student_agg.c_sc or 0),
        "ST": int(student_agg.c_st or 0)
    }
    
    dis_dist = {
        "None": int(student_agg.d_none or 0),
        "Visual": int(student_agg.d_visual or 0),
        "Hearing": int(student_agg.d_hearing or 0),
        "Locomotor": int(student_agg.d_locomotor or 0),
        "Cognitive": int(student_agg.d_cognitive or 0),
        "Multiple": int(student_agg.d_multiple or 0)
    }

    # ── School type distribution ──────────────────────────
    type_dist = {
        t: n for t, n in
        db.query(School.school_type, func.count(School.id))
        .filter(school_filter)
        .group_by(School.school_type)
        .all()
    }

    # ── State-wise inclusion scores ───────────────────────
    state_wise_rows = (
        db.query(
            School.state,
            func.avg(School.inclusion_score).label("avg_inclusion"),
            func.count(School.id).label("school_count"),
        )
        .filter(school_filter)
        .group_by(School.state)
        .order_by(School.state)
        .all()
    )
    state_wise = [
        {
            "state": row.state,
            "avg_inclusion": round(row.avg_inclusion or 0, 1),
            "school_count": row.school_count,
        }
        for row in state_wise_rows
    ]

    # ── Top risk schools (SQL aggregated) ────────────────
    risk_q = (
        db.query(
            Student.school_id,
            func.avg(Student.dropout_risk).label("avg_risk"),
            func.count(Student.id).label("student_count"),
        )
        .group_by(Student.school_id)
        .having(func.avg(Student.dropout_risk) >= 40)
        .order_by(func.avg(Student.dropout_risk).desc())
        .limit(10)
    )
    if state:
        risk_q = risk_q.filter(Student.school_id.in_(student_school_subq))

    risk_rows = risk_q.all()
    risk_school_ids = [r.school_id for r in risk_rows]
    risk_schools = {s.id: s for s in db.query(School).filter(School.id.in_(risk_school_ids)).all()}

    top_risk = [
        {
            "id": r.school_id,
            "name": risk_schools[r.school_id].name if r.school_id in risk_schools else "Unknown",
            "district": risk_schools[r.school_id].district if r.school_id in risk_schools else "",
            "state": risk_schools[r.school_id].state if r.school_id in risk_schools else "",
            "avg_dropout_risk": round(r.avg_risk, 1),
            "student_count": r.student_count,
        }
        for r in risk_rows
        if r.school_id in risk_schools
    ]

    return {
        "total_schools": school_agg.total_schools or 0,
        "total_students": student_agg.total_students or 0,
        "avg_inclusion_score": round(school_agg.avg_inclusion or 0, 1),
        "avg_accessibility_score": round(school_agg.avg_accessibility or 0, 1),
        "dropout_risk_high_count": int(student_agg.high_risk or 0),
        "avg_attendance": round(float(student_agg.avg_attendance or 0), 1),
        "gender_distribution": gender_dist,
        "category_distribution": cat_dist,
        "disability_distribution": dis_dist,
        "school_type_distribution": type_dist,
        "state_wise_inclusion": state_wise,
        "top_risk_schools": top_risk,
    }

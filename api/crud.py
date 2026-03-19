from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
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
def get_teachers(db: Session, school_id: int = None):
    q = db.query(Teacher)
    if school_id:
        q = q.filter(Teacher.school_id == school_id)
    return q.all()


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


# ─── Dashboard Stats ─────────────────────────────────────
def get_dashboard_stats(db: Session, state: str = None):
    school_query = db.query(School)
    if state:
        school_query = school_query.filter(School.state == state)
    schools = school_query.all()

    school_ids = [s.id for s in schools]
    student_query = db.query(Student)
    if school_ids:
        student_query = student_query.filter(Student.school_id.in_(school_ids))
    students = student_query.all()

    total_schools = len(schools)
    total_students = len(students)

    avg_inclusion = round(
        sum(s.inclusion_score for s in schools) / total_schools, 1
    ) if total_schools > 0 else 0

    avg_accessibility = round(
        sum(s.accessibility_score for s in schools) / total_schools, 1
    ) if total_schools > 0 else 0

    high_risk = sum(1 for s in students if s.dropout_risk >= 60)

    avg_attendance = round(
        sum(s.attendance_rate for s in students) / total_students, 1
    ) if total_students > 0 else 0

    # Gender distribution
    gender_dist = {}
    for s in students:
        gender_dist[s.gender] = gender_dist.get(s.gender, 0) + 1

    # Category distribution
    cat_dist = {}
    for s in students:
        cat_dist[s.category] = cat_dist.get(s.category, 0) + 1

    # Disability distribution
    dis_dist = {}
    for s in students:
        dis_dist[s.disability_type] = dis_dist.get(s.disability_type, 0) + 1

    # School type distribution
    type_dist = {}
    for s in schools:
        type_dist[s.school_type] = type_dist.get(s.school_type, 0) + 1

    # State-wise inclusion scores
    state_scores = {}
    state_counts = {}
    for s in schools:
        state_scores[s.state] = state_scores.get(s.state, 0) + s.inclusion_score
        state_counts[s.state] = state_counts.get(s.state, 0) + 1

    state_wise = [
        {"state": st, "avg_inclusion": round(state_scores[st] / state_counts[st], 1),
         "school_count": state_counts[st]}
        for st in sorted(state_scores.keys())
    ]

    # Top risk schools
    top_risk = []
    for school in schools:
        school_students = [s for s in students if s.school_id == school.id]
        if school_students:
            avg_risk = sum(s.dropout_risk for s in school_students) / len(school_students)
            if avg_risk >= 40:
                top_risk.append({
                    "id": school.id,
                    "name": school.name,
                    "district": school.district,
                    "state": school.state,
                    "avg_dropout_risk": round(avg_risk, 1),
                    "student_count": len(school_students),
                })
    top_risk.sort(key=lambda x: x["avg_dropout_risk"], reverse=True)

    return {
        "total_schools": total_schools,
        "total_students": total_students,
        "avg_inclusion_score": avg_inclusion,
        "avg_accessibility_score": avg_accessibility,
        "dropout_risk_high_count": high_risk,
        "avg_attendance": avg_attendance,
        "gender_distribution": gender_dist,
        "category_distribution": cat_dist,
        "disability_distribution": dis_dist,
        "school_type_distribution": type_dist,
        "state_wise_inclusion": state_wise,
        "top_risk_schools": top_risk[:10],
    }

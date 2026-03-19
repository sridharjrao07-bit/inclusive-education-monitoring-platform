"""
Seed data script — generates realistic synthetic data for Indian schools.
Run once to populate the SQLite database.
"""
import random
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import engine, SessionLocal, Base
from models import School, Facility, Student, Teacher, Feedback
from ai_service import predict_dropout_risk

random.seed(42)

# ─── Indian Data Templates ───────────────────────────────
STATES_DISTRICTS = {
    "Uttar Pradesh": ["Lucknow", "Varanasi", "Agra", "Kanpur", "Prayagraj"],
    "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad"],
    "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Salem", "Tiruchirappalli"],
    "Karnataka": ["Bengaluru", "Mysuru", "Hubli", "Mangaluru", "Belgaum"],
    "Bihar": ["Patna", "Gaya", "Muzaffarpur", "Bhagalpur", "Darbhanga"],
    "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur", "Kota", "Ajmer"],
    "Madhya Pradesh": ["Bhopal", "Indore", "Gwalior", "Jabalpur", "Ujjain"],
    "Kerala": ["Thiruvananthapuram", "Kochi", "Kozhikode", "Thrissur", "Kollam"],
    "West Bengal": ["Kolkata", "Howrah", "Siliguri", "Asansol", "Durgapur"],
    "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot", "Gandhinagar"],
    "Odisha": ["Bhubaneswar", "Cuttack", "Rourkela", "Berhampur", "Sambalpur"],
    "Jharkhand": ["Ranchi", "Jamshedpur", "Dhanbad", "Bokaro", "Deoghar"],
    "Andhra Pradesh": ["Visakhapatnam", "Vijayawada", "Guntur", "Tirupati", "Nellore"],
    "Telangana": ["Hyderabad", "Warangal", "Karimnagar", "Nizamabad", "Khammam"],
}

SCHOOL_PREFIXES = [
    "Government Primary School", "Sarvodaya Vidyalaya", "Kendriya Vidyalaya",
    "Jawahar Navodaya Vidyalaya", "Government High School", "Adarsh Vidya Mandir",
    "Rashtriya Madhyamik Shiksha Abhiyan School", "Samagra Shiksha Model School",
    "Kasturba Gandhi Balika Vidyalaya", "District Institute School",
]

FIRST_NAMES_M = [
    "Aarav", "Arjun", "Vihaan", "Aditya", "Sai", "Rohan", "Kartik", "Ravi",
    "Mohit", "Vikram", "Harsh", "Deepak", "Rahul", "Suresh", "Amit",
    "Pranav", "Nikhil", "Ankit", "Gaurav", "Manish",
]
FIRST_NAMES_F = [
    "Aanya", "Aarohi", "Diya", "Priya", "Kavya", "Ananya", "Meera", "Pooja",
    "Sunita", "Rekha", "Shanti", "Lakshmi", "Geeta", "Rani", "Sita",
    "Neha", "Swati", "Divya", "Ritu", "Nisha",
]
LAST_NAMES = [
    "Sharma", "Verma", "Singh", "Kumar", "Patel", "Gupta", "Das", "Reddy",
    "Rao", "Nair", "Yadav", "Joshi", "Iyer", "Pillai", "Mishra",
    "Pandey", "Chauhan", "Thakur", "Bhat", "Patil",
]

TEACHER_NAMES = [
    "Dr. Anand Kumar", "Smt. Savitri Devi", "Shri. Ramesh Prasad",
    "Smt. Lalita Sharma", "Dr. Priya Nair", "Shri. Vikram Singh",
    "Smt. Meena Kumari", "Dr. Suresh Reddy", "Shri. Anil Gupta",
    "Smt. Kavita Iyer", "Dr. Rajan Pillai", "Shri. Manoj Patel",
]

SUBJECTS = ["Mathematics", "Science", "Hindi", "English", "Social Studies",
            "Computer Science", "Physical Education", "Art"]

DISABILITY_TYPES = ["None", "None", "None", "None", "None", "None",  # weighted: mostly None
                    "Visual", "Hearing", "Locomotor", "Cognitive", "Multiple"]

CATEGORIES = ["General", "General", "OBC", "OBC", "SC", "ST"]  # weighted

SOCIO_ECONOMIC = ["BPL", "Lower", "Lower", "Middle", "Middle", "Middle", "Upper"]

FEEDBACK_COMMENTS = [
    "Good school with caring teachers.",
    "Need more accessible facilities.",
    "My child is happy and learning well.",
    "The school lacks proper ramps and washrooms for disabled students.",
    "Teachers are supportive and inclusive.",
    "We need more braille materials.",
    "Transport facility would be very helpful.",
    "The inclusion programs should be expanded.",
    "Overall satisfied with the education quality.",
    "Need improvement in special education training for teachers.",
    "Computer lab needs better equipment.",
    "Library needs more regional language books.",
]


def seed():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    school_id = 0
    all_schools = []

    for state, districts in STATES_DISTRICTS.items():
        for district in districts:
            # 2-3 schools per district
            num_schools = random.randint(2, 3)
            for _ in range(num_schools):
                school_id += 1
                school_type = random.choices(["Rural", "Urban"], weights=[60, 40])[0]
                prefix = random.choice(SCHOOL_PREFIXES)
                name = f"{prefix}, {district}"

                school = School(
                    id=school_id,
                    name=name,
                    district=district,
                    state=state,
                    school_type=school_type,
                    board=random.choice(["State Board", "CBSE", "ICSE"]),
                    medium=random.choice(["Hindi", "English", "Regional"]),
                )
                db.add(school)
                db.flush()

                # ── Facility ──
                # Rural schools: less likely to have facilities
                rural_factor = 0.3 if school_type == "Rural" else 0.7

                facility = Facility(
                    school_id=school_id,
                    has_ramps=random.random() < rural_factor,
                    has_braille_materials=random.random() < (rural_factor * 0.5),
                    has_assistive_tech=random.random() < (rural_factor * 0.4),
                    has_special_educator=random.random() < (rural_factor * 0.6),
                    has_accessible_washroom=random.random() < rural_factor,
                    has_transport=random.random() < (rural_factor * 0.5),
                    has_computer_lab=random.random() < rural_factor,
                    has_library=random.random() < (rural_factor + 0.2),
                )
                db.add(facility)

                # Calculate accessibility score
                features = [
                    facility.has_ramps, facility.has_braille_materials,
                    facility.has_assistive_tech, facility.has_special_educator,
                    facility.has_accessible_washroom, facility.has_transport,
                    facility.has_computer_lab, facility.has_library,
                ]
                school.accessibility_score = round((sum(features) / len(features)) * 100, 1)

                # ── Students (15-50 per school) ──
                num_students = random.randint(15, 50)
                school.total_students = num_students
                student_risks = []

                for _ in range(num_students):
                    gender = random.choices(["Male", "Female", "Other"], weights=[48, 48, 4])[0]
                    if gender == "Male":
                        first = random.choice(FIRST_NAMES_M)
                    elif gender == "Female":
                        first = random.choice(FIRST_NAMES_F)
                    else:
                        first = random.choice(FIRST_NAMES_M + FIRST_NAMES_F)
                    last = random.choice(LAST_NAMES)

                    disability = random.choice(DISABILITY_TYPES)
                    category = random.choice(CATEGORIES)
                    socio = random.choice(SOCIO_ECONOMIC)

                    # Attendance correlated with rural + socio-economic
                    base_att = random.gauss(78, 15)
                    if school_type == "Rural":
                        base_att -= random.uniform(5, 15)
                    if socio == "BPL":
                        base_att -= random.uniform(5, 10)
                    if disability != "None":
                        base_att -= random.uniform(3, 12)
                    attendance = max(20, min(100, round(base_att, 1)))

                    academic = max(15, min(100, round(random.gauss(55, 20), 1)))

                    enrollment = random.choices(
                        ["Active", "Dropout", "Transferred"],
                        weights=[85, 10, 5]
                    )[0]

                    risk = predict_dropout_risk(
                        attendance_rate=attendance,
                        academic_score=academic,
                        disability_type=disability,
                        socio_economic=socio,
                        school_type=school_type,
                        has_ramps=facility.has_ramps,
                        has_assistive_tech=facility.has_assistive_tech,
                        has_special_educator=facility.has_special_educator,
                    )
                    student_risks.append(risk)

                    student = Student(
                        school_id=school_id,
                        name=f"{first} {last}",
                        gender=gender,
                        category=category,
                        disability_type=disability,
                        socio_economic=socio,
                        enrollment_status=enrollment,
                        attendance_rate=attendance,
                        grade_level=random.randint(1, 12),
                        academic_score=academic,
                        dropout_risk=risk,
                    )
                    db.add(student)

                # ── Teachers (3-8 per school) ──
                num_teachers = random.randint(3, 8)
                for _ in range(num_teachers):
                    teacher = Teacher(
                        school_id=school_id,
                        name=random.choice(TEACHER_NAMES),
                        subject=random.choice(SUBJECTS),
                        trained_in_special_ed=random.random() < (rural_factor * 0.5),
                        years_experience=random.randint(1, 30),
                    )
                    db.add(teacher)

                # ── Feedback (1-5 per school) ──
                num_fb = random.randint(1, 5)
                for _ in range(num_fb):
                    fb = Feedback(
                        school_id=school_id,
                        user_role=random.choice(["Parent", "Student", "Teacher"]),
                        rating=random.randint(1, 5),
                        comments=random.choice(FEEDBACK_COMMENTS),
                    )
                    db.add(fb)

                # ── Inclusion score ──
                # Simplified inline calculation
                total_s = num_students
                acc = school.accessibility_score
                diverse_approx = sum(1 for _ in range(num_students) if random.random() < 0.35)
                diversity_score = min((diverse_approx / total_s) * 200, 100) if total_s > 0 else 0
                avg_att = sum(s.attendance_rate for s in db.query(Student).filter(
                    Student.school_id == school_id).all()) / num_students if num_students > 0 else 0
                trained_pct = sum(1 for t in db.query(Teacher).filter(
                    Teacher.school_id == school_id).all() if t.trained_in_special_ed) / num_teachers * 100

                inclusion = (acc * 0.4) + (diversity_score * 0.3) + (avg_att * 0.2) + (trained_pct * 0.1)
                school.inclusion_score = round(inclusion, 1)

                all_schools.append(school)

    db.commit()
    db.close()
    print(f"✅ Seeded {school_id} schools across {len(STATES_DISTRICTS)} states!")
    return school_id


if __name__ == "__main__":
    seed()

"""
import_csv.py — Import 5,000 real school records from the UDISE facility CSV.
Uses bulk inserts and a fast inline heuristic (no ML model) for speed.
School names are set to "School {UDISE_CODE}" since the UDISE portal requires CAPTCHA.
Run: python import_csv.py
"""
import csv
import random
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import engine
from models import School, Facility, Student, Teacher, Feedback, User, Base

random.seed(42)

CSV_PATH = r"C:\Users\sridh\Downloads\4f544f35-10b8-46a3-a6ae-2528edc80097.csv"
LIMIT = 7500  # We want to import all 7,366 school records from the new CSV

SCHOOL_PREFIXES = [
    "Government Primary School", "Sarvodaya Vidyalaya", "Kendriya Vidyalaya",
    "Jawahar Navodaya Vidyalaya", "Government High School", "Adarsh Vidya Mandir",
    "Rashtriya Madhyamik Shiksha Abhiyan School", "Samagra Shiksha Model School",
    "Kasturba Gandhi Balika Vidyalaya", "District Institute School",
]

# ─── Data pools ──────────────────────────────────────────────────
FIRST_NAMES_M = ["Aarav","Arjun","Vihaan","Aditya","Sai","Rohan","Kartik",
                 "Ravi","Mohit","Vikram","Harsh","Deepak","Rahul","Suresh","Amit"]
FIRST_NAMES_F = ["Aanya","Aarohi","Diya","Priya","Kavya","Ananya","Meera",
                 "Pooja","Sunita","Rekha","Shanti","Lakshmi","Geeta","Rani","Nisha"]
LAST_NAMES    = ["Sharma","Verma","Singh","Kumar","Patel","Gupta","Das","Reddy",
                 "Rao","Nair","Yadav","Joshi","Iyer","Pillai","Mishra"]
TEACHER_NAMES = ["Dr. Anand Kumar","Smt. Savitri Devi","Shri. Ramesh Prasad",
                 "Smt. Lalita Sharma","Dr. Priya Nair","Shri. Vikram Singh",
                 "Smt. Meena Kumari","Dr. Suresh Reddy","Shri. Anil Gupta"]
SUBJECTS   = ["Mathematics","Science","Hindi","English","Social Studies","Computer Science"]
DISABILITY = ["None"]*6 + ["Visual","Hearing","Locomotor","Cognitive","Multiple"]
CATEGORIES = ["General","General","OBC","OBC","SC","ST"]
SOCIO      = ["BPL","Lower","Lower","Middle","Middle","Middle","Upper"]
FEEDBACKS  = [
    "Good school with caring teachers.",
    "Need more accessible facilities.",
    "My child is happy and learning well.",
    "The school lacks proper ramps and washrooms for disabled students.",
    "Teachers are supportive and inclusive.",
    "We need more braille materials.",
    "Transport facility would be very helpful.",
    "Overall satisfied with the education quality.",
]


def fast_dropout_risk(att, acad, dis, soc, rural, has_ramps, has_asst, has_sped):
    """Inline heuristic — same logic as ai_service but no ML model overhead."""
    risk = 0.0
    # Attendance
    if att < 40:   risk += 35
    elif att < 60: risk += 28
    elif att < 75: risk += 18
    elif att < 85: risk += 8
    else:           risk += 2
    # Academic
    if acad < 30:   risk += 25
    elif acad < 50: risk += 18
    elif acad < 65: risk += 10
    else:            risk += 3
    # Disability gap
    if dis != "None":
        gap = 20
        if dis in ("Locomotor","Multiple") and has_ramps: gap -= 7
        if has_asst:  gap -= 7
        if has_sped:  gap -= 6
        risk += max(gap, 0)
    else:
        risk += 2
    # Socioeconomic
    risk += {"BPL":10,"Lower":7,"Middle":3,"Upper":1}.get(soc, 3)
    # Rural
    risk += 8 if rural else 2
    return min(round(risk, 1), 100.0)


def safe_int(val, default=0):
    try:
        return int(str(val).strip())
    except (ValueError, AttributeError):
        return default


def import_data():
    t0 = time.time()
    print("Dropping and recreating tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Tables ready.")

    schools = []; facilities = []; students = []; teachers = []; feedbacks = []
    count = 0

    print(f"\nBuilding {LIMIT} records in memory (no network calls)...")
    with open(CSV_PATH, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if count >= LIMIT:
                break
            count += 1

            schcd  = row.get('SCHCD', f'UNK_{count}').strip()
            rural  = random.random() < 0.6
            stype  = "Rural" if rural else "Urban"
            rf     = 0.3 if rural else 0.7

            # Facilities from CSV
            has_ramps = safe_int(row.get('RAMPS_YN','0')) == 1
            has_lib   = safe_int(row.get('LIBRARY_YN','0')) == 1
            has_comp  = safe_int(row.get('COMPUTER','0')) > 0
            has_wc    = safe_int(row.get('TOILETD','0')) > 0
            has_br    = random.random() < rf * 0.5
            has_asst  = random.random() < rf * 0.4
            has_sped  = random.random() < rf * 0.6
            has_trans = random.random() < rf * 0.5

            feat      = [has_ramps, has_br, has_asst, has_sped, has_wc, has_trans, has_comp, has_lib]
            acc       = round(sum(feat)/len(feat)*100, 1)

            num_stu   = random.randint(15, 50)
            num_tea   = random.randint(3, 8)
            atts      = []
            trained_n = 0

            for _ in range(num_stu):
                gender = random.choices(["Male","Female","Other"], weights=[48,48,4])[0]
                first  = random.choice(FIRST_NAMES_M if gender=="Male" else
                                       FIRST_NAMES_F if gender=="Female" else
                                       FIRST_NAMES_M+FIRST_NAMES_F)
                dis  = random.choice(DISABILITY)
                soc  = random.choice(SOCIO)
                att  = random.gauss(78,15)
                if rural:       att -= random.uniform(5,15)
                if soc=="BPL":  att -= random.uniform(5,10)
                if dis!="None": att -= random.uniform(3,12)
                att  = max(20.0, min(100.0, round(att,1)))
                atts.append(att)
                acad = max(15.0, min(100.0, round(random.gauss(55,20),1)))
                enrl = random.choices(["Active","Dropout","Transferred"], weights=[85,10,5])[0]
                risk = fast_dropout_risk(att,acad,dis,soc,rural,has_ramps,has_asst,has_sped)
                students.append(dict(school_id=count, name=f"{first} {random.choice(LAST_NAMES)}",
                    gender=gender, category=random.choice(CATEGORIES), disability_type=dis,
                    socio_economic=soc, enrollment_status=enrl, attendance_rate=att,
                    grade_level=random.randint(1,12), academic_score=acad, dropout_risk=risk))

            for _ in range(num_tea):
                tr = random.random() < rf*0.5
                if tr: trained_n += 1
                teachers.append(dict(school_id=count, name=random.choice(TEACHER_NAMES),
                    subject=random.choice(SUBJECTS), trained_in_special_ed=tr,
                    years_experience=random.randint(1,30)))

            for _ in range(random.randint(1,4)):
                feedbacks.append(dict(school_id=count,
                    user_role=random.choice(["Parent","Student","Teacher"]),
                    rating=random.randint(1,5), comments=random.choice(FEEDBACKS)))

            avg_att    = sum(atts)/len(atts) if atts else 0
            tr_pct     = trained_n/num_tea*100 if num_tea else 0
            div_n      = sum(1 for _ in range(num_stu) if random.random()<0.35)
            diversity  = min(div_n/num_stu*200, 100) if num_stu else 0
            inc        = round(acc*0.4 + diversity*0.3 + avg_att*0.2 + tr_pct*0.1, 1)

            district = row.get('School Disrtict', row.get('School District', 'Unknown')).strip()
            
            try:
                seed_val = int(schcd)
            except Exception:
                seed_val = count
            rng = random.Random(seed_val)
            prefix = rng.choice(SCHOOL_PREFIXES)
            name = f"{prefix}, {district} ({schcd})"

            schools.append(dict(id=count, name=name, district=district,
                state="Karnataka", school_type=stype,
                board=random.choice(["State Board","CBSE","ICSE"]),
                medium=random.choice(["Kannada","English","Hindi"]),
                registration_code=schcd, total_students=num_stu,
                accessibility_score=acc, inclusion_score=inc))

            facilities.append(dict(school_id=count, has_ramps=has_ramps,
                has_braille_materials=has_br, has_assistive_tech=has_asst,
                has_special_educator=has_sped, has_accessible_washroom=has_wc,
                has_transport=has_trans, has_computer_lab=has_comp, has_library=has_lib))

            if count % 500 == 0:
                elapsed = round(time.time()-t0, 1)
                print(f"  {count}/{LIMIT} built in memory ({elapsed}s)...")

    # ─── Mock data for other states ─────────────────────────────────
    STATES_DISTRICTS = {
        "Uttar Pradesh": ["Lucknow", "Varanasi", "Agra", "Kanpur", "Prayagraj"],
        "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad"],
        "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Salem", "Tiruchirappalli"],
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

    print("\nGenerating realistic mock data for other Indian states...")
    mock_count = 0
    for state, districts in STATES_DISTRICTS.items():
        for district in districts:
            # Generate 3-5 schools per district
            num_schools = random.randint(3, 5)
            for _ in range(num_schools):
                count += 1
                mock_count += 1
                
                # Dynamic UDISE prefix based on state
                state_prefix = {
                    "Uttar Pradesh": "09", "Maharashtra": "27", "Tamil Nadu": "33",
                    "Bihar": "10", "Rajasthan": "08", "Madhya Pradesh": "23",
                    "Kerala": "32", "West Bengal": "19", "Gujarat": "24",
                    "Odisha": "21", "Jharkhand": "20", "Andhra Pradesh": "28",
                    "Telangana": "36"
                }.get(state, "99")
                
                schcd = f"{state_prefix}{random.randint(100, 999)}{random.randint(100, 999)}{random.randint(10, 99)}"
                
                rural  = random.random() < 0.6
                stype  = "Rural" if rural else "Urban"
                rf     = 0.3 if rural else 0.7
                
                # Apply state-level accessibility/infrastructure development modifiers
                state_mod = {
                    "Kerala": 0.25, "Tamil Nadu": 0.15, "Maharashtra": 0.1, 
                    "Bihar": -0.15, "Uttar Pradesh": -0.1
                }.get(state, 0.0)
                
                s_rf = max(0.1, min(0.9, rf + state_mod))
                
                has_ramps = random.random() < s_rf
                has_lib   = random.random() < (s_rf + 0.1)
                has_comp  = random.random() < s_rf
                has_wc    = random.random() < (s_rf + 0.2)
                has_br    = random.random() < s_rf * 0.5
                has_asst  = random.random() < s_rf * 0.4
                has_sped  = random.random() < s_rf * 0.6
                has_trans = random.random() < s_rf * 0.5
                
                feat      = [has_ramps, has_br, has_asst, has_sped, has_wc, has_trans, has_comp, has_lib]
                acc       = round(sum(feat)/len(feat)*100, 1)
                
                num_stu   = random.randint(15, 50)
                num_tea   = random.randint(3, 8)
                atts      = []
                trained_n = 0
                
                for _ in range(num_stu):
                    gender = random.choices(["Male","Female","Other"], weights=[48,48,4])[0]
                    first  = random.choice(FIRST_NAMES_M if gender=="Male" else
                                           FIRST_NAMES_F if gender=="Female" else
                                           FIRST_NAMES_M+FIRST_NAMES_F)
                    dis  = random.choice(DISABILITY)
                    soc  = random.choice(SOCIO)
                    
                    # Corelate student attendance with state, rural, and disability factors
                    att  = random.gauss(78,15)
                    if rural:       att -= random.uniform(5,15)
                    if soc=="BPL":  att -= random.uniform(5,10)
                    if dis!="None": att -= random.uniform(3,12)
                    att += state_mod * 15
                    att  = max(20.0, min(100.0, round(att,1)))
                    atts.append(att)
                    
                    acad = random.gauss(55,20) + (state_mod * 10)
                    acad = max(15.0, min(100.0, round(acad,1)))
                    
                    enrl = random.choices(["Active","Dropout","Transferred"], weights=[85,10,5])[0]
                    risk = fast_dropout_risk(att,acad,dis,soc,rural,has_ramps,has_asst,has_sped)
                    students.append(dict(school_id=count, name=f"{first} {random.choice(LAST_NAMES)}",
                        gender=gender, category=random.choice(CATEGORIES), disability_type=dis,
                        socio_economic=soc, enrollment_status=enrl, attendance_rate=att,
                        grade_level=random.randint(1,12), academic_score=acad, dropout_risk=risk))
                
                for _ in range(num_tea):
                    tr = random.random() < s_rf*0.5
                    if tr: trained_n += 1
                    teachers.append(dict(school_id=count, name=random.choice(TEACHER_NAMES),
                        subject=random.choice(SUBJECTS), trained_in_special_ed=tr,
                        years_experience=random.randint(1,30)))
                
                for _ in range(random.randint(1,4)):
                    feedbacks.append(dict(school_id=count,
                        user_role=random.choice(["Parent","Student","Teacher"]),
                        rating=random.randint(1,5), comments=random.choice(FEEDBACKS)))
                
                avg_att    = sum(atts)/len(atts) if atts else 0
                tr_pct     = trained_n/num_tea*100 if num_tea else 0
                div_n      = sum(1 for _ in range(num_stu) if random.random()<0.35)
                diversity  = min(div_n/num_stu*200, 100) if num_stu else 0
                inc        = round(acc*0.4 + diversity*0.3 + avg_att*0.2 + tr_pct*0.1, 1)
                
                # Deterministic beautiful name
                rng = random.Random(int(schcd))
                prefix = rng.choice(SCHOOL_PREFIXES)
                name = f"{prefix}, {district} ({schcd})"
                
                schools.append(dict(id=count, name=name, district=district,
                    state=state, school_type=stype,
                    board=random.choice(["State Board","CBSE","ICSE"]),
                    medium=random.choice(["Hindi","English","Regional"]),
                    registration_code=schcd, total_students=num_stu,
                    accessibility_score=acc, inclusion_score=inc))
                
                facilities.append(dict(school_id=count, has_ramps=has_ramps,
                    has_braille_materials=has_br, has_assistive_tech=has_asst,
                    has_special_educator=has_sped, has_accessible_washroom=has_wc,
                    has_transport=has_trans, has_computer_lab=has_comp, has_library=has_lib))

    print(f"Generated {mock_count} mock schools for other states!")
    print(f"\nAll {count} records built ({count - mock_count} real from CSV, {mock_count} mock for other states). Starting bulk insert into Supabase...")

    def bulk_insert(conn, model, rows, batch_size=500):
        table = model.__table__
        for i in range(0, len(rows), batch_size):
            chunk = rows[i:i+batch_size]
            conn.execute(table.insert(), chunk)
            print(f"    Inserted rows {i+len(chunk)}/{len(rows)}")

    with engine.begin() as conn:
        print("  [1/5] Schools...")
        bulk_insert(conn, School, schools, 500)
        print("  [2/5] Facilities...")
        bulk_insert(conn, Facility, facilities, 500)
        print("  [3/5] Students...")
        bulk_insert(conn, Student, students, 1000)
        print("  [4/5] Teachers...")
        bulk_insert(conn, Teacher, teachers, 1000)
        print("  [5/6] Feedbacks...")
        bulk_insert(conn, Feedback, feedbacks, 1000)

        # Seed default users so that the administration panel remains accessible
        print("  [6/6] Seeding default admin, state_admin, and teacher users...")
        from auth import hash_password
        
        defaults = [
            {"username": "admin", "email": "admin@edu.gov.in", "hashed_password": hash_password("admin123"),
             "role": "national_admin", "state": None, "school_id": None},
            {"username": "state_mp", "email": "mp@edu.gov.in", "hashed_password": hash_password("state123"),
             "role": "state_admin", "state": "Madhya Pradesh", "school_id": None},
            {"username": "teacher1", "email": "teacher1@school.in", "hashed_password": hash_password("teacher123"),
             "role": "teacher", "state": None, "school_id": 1},
        ]
        conn.execute(User.__table__.insert(), defaults)
        print("    Default users successfully seeded!")

    elapsed = round(time.time()-t0, 1)
    print(f"\nDone! Imported {count} schools in {elapsed}s total.")


if __name__ == "__main__":
    import_data()

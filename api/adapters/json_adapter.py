"""
JSON Adapter — Parses government-format JSON data into platform records.

Supports two formats:
1. Flat array: [{ school fields + student fields mixed per row }]
2. Nested:     { "schools": [{ "name":..., "students": [...] }] }
"""
import json
from typing import List, Dict, Any
from . import BaseAdapter


class JSONAdapter(BaseAdapter):
    """Parse government-style JSON into school + student records."""

    def parse(self, raw_data: bytes, filename: str) -> List[Dict[str, Any]]:
        text = raw_data.decode("utf-8-sig")
        data = json.loads(text)

        records = []

        # Format 1: Top-level array of flat records
        if isinstance(data, list):
            for i, item in enumerate(data):
                item["_row"] = i + 1
                item["_type"] = "mixed"
                records.append(item)

        # Format 2: Nested structure with "schools" key
        elif isinstance(data, dict):
            schools = data.get("schools", data.get("data", []))
            if isinstance(schools, list):
                for i, school_data in enumerate(schools):
                    # Extract school record
                    school_rec = {
                        "_row": i + 1,
                        "_type": "school",
                        "school_name": school_data.get("name") or school_data.get("school_name"),
                        "district": school_data.get("district"),
                        "state": school_data.get("state"),
                        "school_type": school_data.get("school_type") or school_data.get("type", "Urban"),
                        "board": school_data.get("board", "State Board"),
                        "medium": school_data.get("medium", "Hindi"),
                    }

                    # Extract facility data
                    facility = school_data.get("facility", school_data.get("facilities", {}))
                    if isinstance(facility, dict):
                        for key in ["has_ramps", "has_braille_materials", "has_assistive_tech",
                                    "has_special_educator", "has_accessible_washroom",
                                    "has_transport", "has_computer_lab", "has_library"]:
                            school_rec[key] = bool(facility.get(key, False))

                    records.append(school_rec)

                    # Extract students
                    students = school_data.get("students", [])
                    for j, student in enumerate(students):
                        student_rec = {
                            "_row": f"{i+1}.{j+1}",
                            "_type": "student",
                            "_school_ref": i,  # links to parent school
                            "student_name": student.get("name") or student.get("student_name"),
                            "gender": student.get("gender", "Other"),
                            "category": student.get("category", "General"),
                            "disability_type": student.get("disability_type", "None"),
                            "socio_economic": student.get("socio_economic", "Middle"),
                            "enrollment_status": student.get("enrollment_status", "Active"),
                            "attendance_rate": float(student.get("attendance_rate", 75.0)),
                            "grade_level": int(student.get("grade_level", 1)),
                            "academic_score": float(student.get("academic_score", 50.0)),
                        }
                        records.append(student_rec)

        return records

    def validate(self, records: List[Dict[str, Any]]) -> tuple:
        valid = []
        errors = []

        for rec in records:
            row = rec.get("_row", "?")
            rec_type = rec.get("_type", "mixed")

            if rec_type in ("school", "mixed"):
                if not rec.get("school_name"):
                    errors.append(f"Record {row}: missing school_name")
                    continue
                if not rec.get("state"):
                    errors.append(f"Record {row}: missing state")
                    continue
                rec.setdefault("district", "Unknown")
                rec.setdefault("school_type", "Urban")

            if rec_type == "student":
                if not rec.get("student_name"):
                    errors.append(f"Record {row}: missing student_name")
                    continue

            valid.append(rec)

        return valid, errors

"""
CSV Adapter — Parses UDISE+ style CSV data into platform records.

Expected CSV columns (flexible — adapter maps whatever is found):
  school_name, district, state, school_type, board, medium,
  has_ramps, has_braille_materials, has_assistive_tech, has_special_educator,
  has_accessible_washroom, has_transport, has_computer_lab, has_library,
  student_name, gender, category, disability_type, socio_economic,
  enrollment_status, attendance_rate, grade_level, academic_score
"""
import csv
import io
from typing import List, Dict, Any
from . import BaseAdapter


# Column name aliases — maps various header spellings to canonical names
COLUMN_ALIASES = {
    # School fields
    "school_name": "school_name", "school name": "school_name", "name": "school_name",
    "schname": "school_name", "sch_name": "school_name",
    "district": "district", "dist": "district", "district_name": "district",
    "state": "state", "state_name": "state",
    "school_type": "school_type", "type": "school_type", "rural_urban": "school_type",
    "location": "school_type",
    "board": "board", "board_name": "board",
    "medium": "medium", "medium_of_instruction": "medium",
    # Facility fields
    "has_ramps": "has_ramps", "ramp": "has_ramps", "ramps": "has_ramps",
    "has_braille_materials": "has_braille_materials", "braille": "has_braille_materials",
    "has_assistive_tech": "has_assistive_tech", "assistive_tech": "has_assistive_tech",
    "has_special_educator": "has_special_educator", "special_educator": "has_special_educator",
    "spl_educator": "has_special_educator",
    "has_accessible_washroom": "has_accessible_washroom", "accessible_washroom": "has_accessible_washroom",
    "has_transport": "has_transport", "transport": "has_transport",
    "has_computer_lab": "has_computer_lab", "computer_lab": "has_computer_lab",
    "has_library": "has_library", "library": "has_library",
    # Student fields
    "student_name": "student_name", "student": "student_name",
    "gender": "gender", "sex": "gender",
    "category": "category", "caste_category": "category", "social_category": "category",
    "disability_type": "disability_type", "disability": "disability_type",
    "cwsn_type": "disability_type",
    "socio_economic": "socio_economic", "economic_status": "socio_economic",
    "enrollment_status": "enrollment_status", "enrollment": "enrollment_status",
    "attendance_rate": "attendance_rate", "attendance": "attendance_rate",
    "grade_level": "grade_level", "grade": "grade_level", "class": "grade_level",
    "academic_score": "academic_score", "score": "academic_score", "marks": "academic_score",
}

SCHOOL_FIELDS = {"school_name", "district", "state", "school_type", "board", "medium"}
FACILITY_FIELDS = {
    "has_ramps", "has_braille_materials", "has_assistive_tech",
    "has_special_educator", "has_accessible_washroom", "has_transport",
    "has_computer_lab", "has_library",
}
STUDENT_FIELDS = {
    "student_name", "gender", "category", "disability_type",
    "socio_economic", "enrollment_status", "attendance_rate",
    "grade_level", "academic_score",
}


def _parse_bool(val: str) -> bool:
    return val.strip().lower() in ("yes", "true", "1", "y", "available")


def _normalize_headers(headers: List[str]) -> Dict[str, str]:
    """Map raw CSV headers to canonical field names."""
    mapping = {}
    for h in headers:
        key = h.strip().lower().replace("-", "_").replace(" ", "_")
        canonical = COLUMN_ALIASES.get(key)
        if canonical:
            mapping[h] = canonical
    return mapping


class CSVAdapter(BaseAdapter):
    """Parse UDISE+-style CSVs into school + student records."""

    def parse(self, raw_data: bytes, filename: str) -> List[Dict[str, Any]]:
        text = raw_data.decode("utf-8-sig")  # handle BOM
        reader = csv.DictReader(io.StringIO(text))

        if not reader.fieldnames:
            return []

        header_map = _normalize_headers(reader.fieldnames)
        records = []

        for row_num, row in enumerate(reader, start=2):
            record = {"_row": row_num, "_type": "mixed"}
            for raw_col, canonical in header_map.items():
                val = row.get(raw_col, "").strip()

                # Type coercion
                if canonical in FACILITY_FIELDS:
                    record[canonical] = _parse_bool(val)
                elif canonical in ("attendance_rate", "academic_score"):
                    try:
                        record[canonical] = float(val) if val else None
                    except ValueError:
                        record[canonical] = None
                elif canonical == "grade_level":
                    try:
                        record[canonical] = int(val) if val else None
                    except ValueError:
                        record[canonical] = None
                else:
                    record[canonical] = val if val else None

            records.append(record)

        return records

    def validate(self, records: List[Dict[str, Any]]) -> tuple:
        valid = []
        errors = []

        for rec in records:
            row = rec.get("_row", "?")

            # Must have at least school_name + state to create a school
            if not rec.get("school_name"):
                errors.append(f"Row {row}: missing school_name")
                continue
            if not rec.get("state"):
                errors.append(f"Row {row}: missing state")
                continue

            # Default values
            rec.setdefault("district", "Unknown")
            rec.setdefault("school_type", "Urban")
            rec.setdefault("board", "State Board")
            rec.setdefault("medium", "Hindi")

            # Student defaults
            if rec.get("student_name"):
                rec.setdefault("gender", "Other")
                rec.setdefault("category", "General")
                rec.setdefault("disability_type", "None")
                rec.setdefault("socio_economic", "Middle")
                rec.setdefault("enrollment_status", "Active")
                rec.setdefault("attendance_rate", 75.0)
                rec.setdefault("grade_level", 1)
                rec.setdefault("academic_score", 50.0)

            valid.append(rec)

        return valid, errors

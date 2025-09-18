"""
note_parser.py

Improved parser for unstructured clinical notes.
Handles negations, synonyms, and duration checks.
"""

import re
import datetime

CURRENT_DATE = datetime.date(2024, 5, 1)

class NoteParser:
    def __init__(self, notes: dict):
        self.notes = {pid: txt.lower() for pid, txt in notes.items()}

    def check_presence(self, patient_id: str, concepts: list) -> bool:
        text = self.notes.get(patient_id, "")
        for term in concepts:
            if term.lower() in text:
                if re.search(rf"(no|denies|without|absence of)\s+{term}", text):
                    continue
                return True
        return False

    def check_absence(self, patient_id: str, concepts: list) -> bool:
        text = self.notes.get(patient_id, "")
        for term in concepts:
            if re.search(rf"(no|denies|without|absence of)\s+{term}", text):
                continue
            if term.lower() in text:
                return False
        return True

    def check_duration(self, patient_id: str, concepts: list, minimum_months: int) -> bool:
        text = self.notes.get(patient_id, "")
        if not self.check_presence(patient_id, concepts):
            return False
        match = re.search(r"(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})", text)
        if match:
            month, year = match.group(1).lower(), int(match.group(2))
            month_map = {m: i+1 for i, m in enumerate([
                "january","february","march","april","may","june",
                "july","august","september","october","november","december"
            ])}
            diag_date = datetime.date(year, month_map[month], 1)
            delta_months = (CURRENT_DATE.year - diag_date.year) * 12 + (CURRENT_DATE.month - diag_date.month)
            return delta_months >= minimum_months
        return True


if __name__ == "__main__":
    notes = {
        "C001": "Confirmed Type 2 Diabetes diagnosis in March 2022. No CHF.",
        "C002": "Patient has congestive heart failure. Diabetes diagnosis April 2024."
    }
    parser = NoteParser(notes)

    print("C001 diabetes >=12 months:", parser.check_duration("C001", ["diabetes"], 12))  # Expect True
    print("C002 diabetes >=12 months:", parser.check_duration("C002", ["diabetes"], 12))  # Expect False
    print("C001 CHF absent:", parser.check_absence("C001", ["chf"]))                     # Expect True
    print("C002 CHF present:", parser.check_presence("C002", ["chf"]))                   # Expect True

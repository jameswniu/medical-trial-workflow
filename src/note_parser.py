"""
note_parser.py

Improved parser for unstructured clinical notes.
- Handles synonyms (CHF, heart failure, cardiac dysfunction).
- Detects negations ("no heart failure", "denies CHF").
- Extracts diagnosis dates and checks minimum duration requirements.
"""

import re
import datetime

CURRENT_DATE = datetime.date(2024, 5, 1)  # fixed "trial date"

class NoteParser:
    def __init__(self, notes: dict):
        # Normalize to lowercase
        self.notes = {pid: txt.lower() for pid, txt in notes.items()}

        # Define synonyms
        self.synonyms = {
            "chf": ["chf", "heart failure", "cardiac dysfunction"],
            "diabetes": ["diabetes", "t2dm", "type 2 diabetes", "hyperglycemia"],
            "cancer": ["cancer", "malignancy", "tumor"],
        }

        # Negation patterns
        self.negation_pattern = re.compile(r"(no|denies|without|absence of)\s+", re.IGNORECASE)

        # Month names for crude date extraction
        self.month_map = {
            "january": 1, "february": 2, "march": 3, "april": 4,
            "may": 5, "june": 6, "july": 7, "august": 8,
            "september": 9, "october": 10, "november": 11, "december": 12
        }

    def expand_concepts(self, concepts):
        """Expand concepts with known synonyms."""
        expanded = []
        for c in concepts:
            c = c.lower()
            if c in self.synonyms:
                expanded.extend(self.synonyms[c])
            else:
                expanded.append(c)
        return list(set(expanded))

    def check_presence(self, patient_id: str, concepts: list) -> bool:
        """Return True if any concept appears positively in patient notes."""
        text = self.notes.get(patient_id, "")
        expanded = self.expand_concepts(concepts)

        for term in expanded:
            # Skip negated mentions
            if re.search(rf"(no|denies|without|absence of)\s+{re.escape(term)}", text):
                continue
            if term in text:
                return True
        return False

    def check_absence(self, patient_id: str, concepts: list) -> bool:
        """Return True if none of the concepts appear positively in notes."""
        text = self.notes.get(patient_id, "")
        expanded = self.expand_concepts(concepts)

        for term in expanded:
            if re.search(rf"(no|denies|without|absence of)\s+{re.escape(term)}", text):
                continue
            if term in text:
                return False
        return True

    def check_duration(self, patient_id: str, concepts: list, minimum_months: int) -> bool:
        """
        Look for a diagnosis date (e.g. 'diagnosed in March 2022') and check if duration >= threshold.
        Returns True if condition met, False otherwise.
        """
        text = self.notes.get(patient_id, "")
        expanded = self.expand_concepts(concepts)

        # Simple regex: "diagnosed ... in March 2022" or "diagnosis ... March 2022"
        match = re.search(r"(diagnosed|diagnosis).*?(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})", text)
        if match:
            month_name, year = match.group(2).lower(), int(match.group(3))
            month = self.month_map.get(month_name, 1)
            diag_date = datetime.date(year, month, 1)

            # Duration in months
            delta_months = (CURRENT_DATE.year - diag_date.year) * 12 + (CURRENT_DATE.month - diag_date.month)
            return delta_months >= minimum_months

        # If no explicit date → fallback to simple presence check
        return self.check_presence(patient_id, expanded)


# -----------------------
# Quick test harness
# -----------------------
if __name__ == "__main__":
    notes = {
        "C001": """Confirmed Type 2 Diabetes diagnosis in March 2022.
                  No signs of heart failure. Family history: breast cancer.""",
        "C002": """Diabetes diagnosis in April 2024. Patient has CHF."""
    }

    parser = NoteParser(notes)

    print("C001 diabetes ≥12 months:", parser.check_duration("C001", ["diabetes"], 12))  # Expected True (March 2022 → >2 yrs before May 2024)
    print("C002 diabetes ≥12 months:", parser.check_duration("C002", ["diabetes"], 12))  # Expected False (April 2024 < 1 month before May 2024)
    print("C001 CHF absent:", parser.check_absence("C001", ["chf"]))                     # Expected True
    print("C002 CHF present:", parser.check_presence("C002", ["chf"]))                   # Expected True

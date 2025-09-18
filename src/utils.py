"""
utils.py

Utility functions for patient data processing:
- calculate_age
- calculate_bmi
"""

import datetime

CURRENT_DATE = datetime.date(2024, 5, 1)

def calculate_age(dob: str) -> int:
    """Calculate age in years from YYYY-MM-DD string. Return None if invalid."""
    try:
        dob = datetime.datetime.strptime(dob, "%Y-%m-%d").date()
        return (CURRENT_DATE - dob).days // 365
    except Exception:
        return None

def calculate_bmi(weight: float, height: float) -> float:
    """Compute BMI = weight / height^2. Return None if invalid."""
    try:
        if not weight or not height or height <= 0:
            return None
        return weight / (height ** 2)
    except Exception:
        return None


if __name__ == "__main__":
    print("Age test:", calculate_age("1965-01-01"))
    # Expected: 59 (as of 2024-05-01)

    print("Age invalid:", calculate_age("BAD"))
    # Expected: None (invalid date string)

    print("BMI test:", calculate_bmi(80, 1.75))
    # Expected: ~26.1

    print("BMI invalid:", calculate_bmi(80, 0))
    # Expected: None (height = 0 invalid)


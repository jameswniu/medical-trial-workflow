"""
utils.py

Utility functions for the medical trial workflow.

Responsibilities:
- Get latest lab values from patient profiles.
- Check recency of events (time window logic).
- Write structured JSON outputs for each protocol.
- Ensure evidence strings always follow the format:
  PASS/FAIL/MAYBE (reason/explanation)

Usage:
    python utils.py
"""

import os
import json
from datetime import datetime


def get_latest_lab(patient: dict, lab_name: str):
    """Return latest lab entry for a patient, or None if not available."""
    return patient.get("latest_labs", {}).get(lab_name)


def most_recent_within(patient: dict, lab_name: str, days: int) -> bool:
    """
    Check if the most recent lab is within the given number of days.
    """
    lab = get_latest_lab(patient, lab_name)
    if not lab or not lab.get("date"):
        return False
    return (datetime.now() - lab["date"]).days <= days


def format_evidence(label: str, explanation: str) -> str:
    """
    Format evidence consistently.
    Example: PASS (Age 56 is between 40 and 70 on 2024-05-01)
    """
    return f"{label} ({explanation})"


def write_json(protocol_id: str, results: list, out_dir="outputs"):
    """
    Write evaluation results to JSON file.
    One file per protocol, containing all patient results.
    """
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{protocol_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    return path


if __name__ == "__main__":
    # Demo test for utils
    dummy_patient = {
        "patient_id": "xyz-789",
        "latest_labs": {
            "HbA1c": {"value": 8.1, "date": datetime(2024, 9, 15)}
        },
    }

    print("Latest HbA1c:", get_latest_lab(dummy_patient, "HbA1c"))
    print("HbA1c recent within 180 days:", most_recent_within(dummy_patient, "HbA1c", 180))
    print("Evidence:", format_evidence("PASS", "Age 56 is between 40 and 70 on 2024-05-01"))

    # Expected:
    # Latest HbA1c: {'value': 8.1, 'date': datetime(2024, 9, 15, 0, 0)}
    # HbA1c recent within 180 days: False
    # Evidence: PASS (Age 56 is between 40 and 70 on 2024-05-01)

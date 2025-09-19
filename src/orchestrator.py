"""
orchestrator.py

Coordinates the medical trial workflow:
- Loads patient profiles (demographics + labs).
- Normalizes trial protocols (structured/unstructured).
- Evaluates patients against protocols.
- Writes explainable JSON outputs.

Usage:
    python orchestrator.py
"""

import os
from data_loader import build_patient_profiles
from protocol_sorter import sort_protocols
from protocol_evaluator import evaluate_patient
from utils import write_json


def run_workflow(patients_csv: str, labs_csv: str, protocols_dir: str, outputs_dir="outputs"):
    """
    Full workflow runner.
    - patients_csv: path to patients.csv
    - labs_csv: path to lab_results.csv
    - protocols_dir: path to YAML protocols directory
    - outputs_dir: where JSON results are saved
    """
    # 1. Load patient profiles
    patients = build_patient_profiles(patients_csv, labs_csv)
    print(f"Loaded {len(patients)} patient profiles")

    # 2. Normalize and load protocols
    protocols = sort_protocols(protocols_dir)
    print(f"Loaded {len(protocols)} normalized protocols")

    # 3. Evaluate each patient against each protocol
    for protocol in protocols:
        results = []
        for patient in patients.values():
            result = evaluate_patient(patient, {
                "id": protocol["protocol_id"],
                "structured": protocol.get("structured_criteria", []),
                "unstructured": protocol.get("unstructured_criteria", []),
            })
            results.append(result)

        # 4. Write per-protocol JSON file
        out_path = write_json(protocol["protocol_id"], results, out_dir=outputs_dir)
        print(f"Saved results for {protocol['protocol_id']} -> {out_path}")


if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    patients_csv = os.path.join(BASE_DIR, "assignment_data", "patients.csv")
    labs_csv = os.path.join(BASE_DIR, "assignment_data", "lab_results.csv")
    protocols_dir = os.path.join(BASE_DIR, "assignment_data")

    run_workflow(patients_csv, labs_csv, protocols_dir)

    # Expected console output:
    # Loaded 50 patient profiles
    # Loaded 3 normalized protocols
    # Saved results for protocol_001 -> outputs/protocol_001.json
    #
    # Example JSON (inside outputs/protocol_001.json):
    # {
    #   "patient_id": "xyz-789",
    #   "is_eligible": false,
    #   "confidence_score": 0.95,
    #   "evidence": {
    #     "age": "PASS (age 56 is between 40 and 70)",
    #     "HbA1c": "PASS (HbA1c 8.1 >= 7.5)",
    #     "is_smoker": "PASS (is_smoker exactly False)",
    #     "diabetes": "MAYBE (notes mention 'borderline sugar', possible diabetes)",
    #     "CHF": "MAYBE (notes mention 'EF 35%', possible CHF)"
    #   }
    # }

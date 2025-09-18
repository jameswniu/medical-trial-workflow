"""
orchestrator.py

Runs the full workflow:
- Loads enriched patient profiles (demographics + labs).
- Indexes clinical notes into the vector DB.
- Loads all cleaned YAML protocols.
- Evaluates patients against each protocol.
- Computes confidence scores (PASS=1.0, FAIL=0.0, MAYBE=0.5).
- Ensures evidence covers all criteria.
- Saves results as JSON in /output.
"""

import os
import json
import yaml
from data_loader import build_patient_profiles
from note_parser import index_clinical_notes
from protocol_evaluator import evaluate_patient

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
ASSIGNMENT_DIR = os.path.join(BASE_DIR, "assignment_data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
NOTES_DIR = os.path.join(ASSIGNMENT_DIR, "clinical_notes")


def compute_confidence(evidence: dict) -> float:
    """
    Compute confidence score from evidence.
    - PASS = 1.0
    - FAIL = 0.0
    - MAYBE = 0.5
    - Unstructured with similarity: use sim value for PASS, (1-sim) for FAIL, 0.5 for MAYBE
    """
    scores = []
    for v in evidence.values():
        if v.startswith("PASS") and "sim=" not in v:
            scores.append(1.0)
        elif v.startswith("FAIL") and "sim=" not in v:
            scores.append(0.0)
        elif v.startswith("MAYBE"):
            scores.append(0.5)
        elif "sim=" in v:
            try:
                sim_val = float(v.split("sim=")[-1].strip(")"))
                if v.startswith("PASS"):
                    scores.append(sim_val)
                elif v.startswith("FAIL"):
                    scores.append(1 - sim_val)
                elif v.startswith("MAYBE"):
                    scores.append(0.5)
            except Exception:
                scores.append(0.5)
        else:
            scores.append(0.5)
    return round(sum(scores) / len(scores), 3) if scores else 0.0


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    patients_csv = os.path.join(ASSIGNMENT_DIR, "patients.csv")
    labs_csv = os.path.join(ASSIGNMENT_DIR, "lab_results.csv")
    profiles = build_patient_profiles(patients_csv, labs_csv)

    print(f"Indexing clinical notes from: {NOTES_DIR}")
    index_clinical_notes(NOTES_DIR)

    protocol_files = [
        os.path.join(ASSIGNMENT_DIR, f)
        for f in os.listdir(ASSIGNMENT_DIR)
        if f.startswith("protocol_") and f.endswith("_clean.yaml")
    ]

    summary = {}

    for proto_file in protocol_files:
        with open(proto_file, "r", encoding="utf-8") as f:
            protocol = yaml.safe_load(f)

        protocol_id = protocol.get("protocol_id", "UNKNOWN")
        study_name = protocol.get("study_name", "Unnamed Study")

        structured = protocol.get("structured_criteria", [])
        unstructured = protocol.get("unstructured_criteria", [])
        criteria_descriptions = [c.get("description", "") for c in structured + unstructured]
        total_criteria = len(criteria_descriptions)

        results = []
        eligible_count = 0

        for pid, patient in profiles.items():
            ok, evidence = evaluate_patient(patient, protocol)

            # Fill missing criteria with "Not evaluated"
            for crit in criteria_descriptions:
                if crit not in evidence:
                    evidence[crit] = "Not evaluated"

            confidence = compute_confidence(evidence)
            results.append({
                "patient_id": pid,
                "is_eligible": ok,
                "confidence_score": confidence,
                "evidence": evidence,
            })
            if ok:
                eligible_count += 1

        out_path = os.path.join(OUTPUT_DIR, f"{protocol_id}_results.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({
                "protocol_id": protocol_id,
                "study_name": study_name,
                "criteria_count": total_criteria,
                "criteria_descriptions": criteria_descriptions,
                "patients": results,
            }, f, indent=2)

        print(f"Finished {protocol_id} ({study_name}) -> {out_path}")
        summary[protocol_id] = {
            "patients": len(results),
            "criteria": total_criteria,
            "eligible": eligible_count,
        }

    print("\nProtocol Summary:")
    for proto_id, info in summary.items():
        pct = round((info['eligible'] / info['patients']) * 100, 1) if info['patients'] else 0
        print(f"- {proto_id}: {info['patients']} patients, {info['criteria']} criteria each, "
              f"{info['eligible']} eligible ({pct}%)")


if __name__ == "__main__":
    main()
    # === Expected Output (example, will vary with patient data) ===
    #
    # Console prints something like:
    #   Indexing clinical notes from: /path/to/assignment_data/clinical_notes
    #   Finished ONC-003-Prevention (Metabolic Factors in Cancer Prevention Study) -> output/ONC-003-Prevention_results.json
    #   Finished RESP-005-Cessation (Advanced Smoking Cessation & Respiratory Health Study) -> output/RESP-005-Cessation_results.json
    #
    # Two JSON files appear in /output/, each with:
    # {
    #   "protocol_id": "ONC-003-Prevention",
    #   "study_name": "Metabolic Factors in Cancer Prevention Study",
    #   "criteria_count": 9,
    #   "criteria_descriptions": [...],
    #   "patients": [
    #       {
    #           "patient_id": "patient_C001",
    #           "is_eligible": true,
    #           "confidence_score": 0.77,
    #           "evidence": {
    #               "Age between 50 and 70 years (inclusive).": "PASS (Age 54 in range 50-70)",
    #               "HbA1c level must be less than 8.0%.": "PASS (HbA1c=7.9, lt 8.0)",
    #               "No personal history of malignancy.": "PASS (no strong match, sim=0.30)",
    #               "...": "..."
    #           }
    #       },
    #       ...
    #   ]
    # }
    #
    # Final summary in console:
    # Protocol Summary:
    # - ONC-003-Prevention: 25 patients, 9 criteria each, 14 eligible (56.0%)
    # - RESP-005-Cessation: 25 patients, 12 criteria each, 18 eligible (72.0%)


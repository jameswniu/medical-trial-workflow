"""
orchestrator.py

Runs the full pipeline:
- Loads patient, lab, and note data.
- Loads all YAML protocols (auto-fixed by DataLoader).
- Evaluates patients against each protocol.
- Saves results as JSON in /output.
"""

import os
import json
from data_loader import DataLoader
from note_parser import NoteParser
from protocol_evaluator import ProtocolEvaluator

BASE_PATH = os.path.join(os.path.dirname(__file__), "..", "assignment_data")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    loader = DataLoader(BASE_PATH)
    patients = loader.load_patients()
    labs = loader.load_lab_results()
    notes = loader.load_clinical_notes()

    note_parser = NoteParser(notes)
    evaluator = ProtocolEvaluator(patients, labs, note_parser)

    protocols = loader.load_all_protocols()

    summary = {"valid": 0, "invalid": 0, "missing": 0, "error": 0}

    for protocol in protocols:
        results = evaluator.evaluate(protocol)
        output = {
            "protocol_id": protocol.get("protocol_id", "unknown"),
            "study_name": protocol.get("study_name", "N/A"),
            "protocol_status": protocol.get("protocol_status", "unknown"),
            "patients": results
        }

        status = output["protocol_status"]
        summary[status] = summary.get(status, 0) + 1

        out_path = os.path.join(OUTPUT_DIR, f"{output['protocol_id']}_results.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)

        print(f"Finished {output['protocol_id']} (status={status}) -> {out_path}")

    print("\nProtocol Summary:")
    for k, v in summary.items():
        print(f"- {k}: {v}")


if __name__ == "__main__":
    main()
    # Expected:
    # - Console prints:
    #   Finished ONC-003-Prevention (status=valid) -> output/ONC-003-Prevention_results.json
    #   Finished RESP-005-Cessation (status=valid) -> output/RESP-005-Cessation_results.json
    # - Two JSON files created in /output, each with:
    #   protocol_id, study_name, protocol_status, and patients list with eligibility evidence
    # - Final summary:
    #   Protocol Summary:
    #   - valid: 2
    #   - invalid: 0
    #   - missing: 0
    #   - error: 0


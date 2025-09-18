"""
data_loader.py

Loads patients (CSV), lab results (CSV), clinical notes (TXT), and trial protocols (YAML).
Protocols are auto-fixed if criteria lists float without parent keys.
"""

import pandas as pd
import os
import yaml

class DataLoader:
    def __init__(self, base_path: str):
        self.base_path = os.path.abspath(base_path)

    def load_patients(self):
        path = os.path.join(self.base_path, "patients.csv")
        if not os.path.exists(path):
            print("patients.csv not found")
            return pd.DataFrame()
        return pd.read_csv(path)

    def load_lab_results(self):
        path = os.path.join(self.base_path, "lab_results.csv")
        if not os.path.exists(path):
            print("lab_results.csv not found")
            return pd.DataFrame()
        return pd.read_csv(path)

    def load_clinical_notes(self):
        notes_dir = os.path.join(self.base_path, "clinical_notes")
        notes = {}
        if not os.path.exists(notes_dir):
            print("clinical_notes folder missing")
            return notes
        for f in os.listdir(notes_dir):
            if f.endswith(".txt"):
                pid = f.replace(".txt", "")
                with open(os.path.join(notes_dir, f), "r", encoding="utf-8") as file:
                    notes[pid] = file.read()
        return notes

    def _auto_fix_yaml(self, text: str) -> str:
        """If criteria start with '- description:' and no parent, wrap under 'structured_criteria:'."""
        lines = text.splitlines(keepends=True)
        fixed, inserted = [], False
        for line in lines:
            if not inserted and line.lstrip().startswith("- description:"):
                fixed.append("structured_criteria:\n")
                inserted = True
            fixed.append(line)
        return "".join(fixed)

    def _fallback_protocol(self, filename: str, status: str, note: str) -> dict:
        """Return a fallback protocol object when YAML cannot be parsed."""
        base = filename.replace(".yaml", "").replace(".yml", "")
        return {
            "protocol_id": base,
            "study_name": note,
            "structured_criteria": [],
            "unstructured_criteria": [],
            "protocol_status": status,
        }

    def load_protocol(self, filepath: str) -> dict:
        """Load a single YAML protocol with auto-fix and error handling."""
        filename = os.path.basename(filepath)
        if not os.path.exists(filepath):
            return self._fallback_protocol(filename, "missing", "File missing")

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                raw = f.read()
            fixed = self._auto_fix_yaml(raw)
            data = yaml.safe_load(fixed)

            if not isinstance(data, dict):
                raise yaml.YAMLError("Parsed YAML not dictionary")

            data.setdefault("structured_criteria", [])
            data.setdefault("unstructured_criteria", [])
            data["protocol_status"] = "valid"
            return data

        except yaml.YAMLError as e:
            print(f"YAML error in {filename}: {e}")
            return self._fallback_protocol(filename, "invalid", "Invalid YAML")
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return self._fallback_protocol(filename, "error", "Unexpected error")

    def load_all_protocols(self):
        """Load all YAML protocol files in assignment_data folder."""
        protocols = []
        for f in os.listdir(self.base_path):
            if f.endswith(".yaml") or f.endswith(".yml"):
                filepath = os.path.join(self.base_path, f)
                proto = self.load_protocol(filepath)
                protocols.append(proto)
        return protocols


if __name__ == "__main__":
    BASE_PATH = os.path.join(os.path.dirname(__file__), "..", "assignment_data")
    loader = DataLoader(BASE_PATH)

    patients = loader.load_patients()
    print("Patients:", patients.head())
    # Expected: First 5 rows of patients.csv (patient_id, date_of_birth, gender, etc.)

    labs = loader.load_lab_results()
    print("Labs:", labs.head())
    # Expected: First 5 rows of lab_results.csv (patient_id, test_name, value, date)

    notes = loader.load_clinical_notes()
    print("Notes sample:", {k: v[:40] + "..." for k, v in list(notes.items())[:2]})
    # Expected: Dictionary with first 2 patient notes truncated

    protocols = loader.load_all_protocols()
    print("Loaded protocols:")
    for proto in protocols:
        print(f"- {proto.get('protocol_id')} ({proto.get('protocol_status')})")
    # Expected: A list of protocol IDs with status "valid" (auto-fixed) or "invalid"


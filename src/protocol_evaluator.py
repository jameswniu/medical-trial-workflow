"""
protocol_evaluator.py

Evaluates patients against YAML-defined clinical trial protocols.
Ensures each criterion generates evidence: PASS, FAIL, or MAYBE.
"""

import pandas as pd
from utils import calculate_age, calculate_bmi

class ProtocolEvaluator:
    def __init__(self, patients, labs, note_parser):
        self.patients = patients
        self.labs = labs
        self.notes = note_parser

    def evaluate(self, protocol: dict):
        results = []

        structured = protocol.get("structured_criteria", [])
        unstructured = protocol.get("unstructured_criteria", [])
        total_criteria = len(structured) + len(unstructured)

        for _, row in self.patients.iterrows():
            patient_id = row.get("patient_id")
            evidence, score, passed = {}, 0, 0

            # --- Structured criteria ---
            for crit in structured:
                desc = crit.get("description", crit.get("type", "criterion"))
                key = desc.lower().replace(" ", "_")[:50]

                ctype = crit.get("type")
                condition = crit.get("condition")

                if ctype == "age":
                    age = calculate_age(row.get("date_of_birth", ""))
                    lo, hi = crit["value"]
                    if age is None:
                        evidence[key] = "MAYBE (DOB missing)"
                    elif lo <= age <= hi:
                        evidence[key] = f"PASS (Age {age} within {lo}-{hi})"
                        score += 1; passed += 1
                    else:
                        evidence[key] = f"FAIL (Age {age} not in {lo}-{hi})"

                elif ctype == "calculated_metric" and crit.get("metric") == "BMI":
                    weight = self.labs.query("patient_id == @patient_id and lab_test_name == 'weight'")["value"].mean()
                    height = self.labs.query("patient_id == @patient_id and lab_test_name == 'height'")["value"].mean()
                    bmi = calculate_bmi(weight, height)
                    lo, hi = crit["value"]
                    if bmi is None:
                        evidence[key] = "MAYBE (weight/height missing)"
                    elif lo <= bmi <= hi:
                        evidence[key] = f"PASS (BMI {bmi:.1f} within {lo}-{hi})"
                        score += 1; passed += 1
                    else:
                        evidence[key] = f"FAIL (BMI {bmi:.1f} outside {lo}-{hi})"

                elif ctype == "demographic":
                    field = crit.get("field")
                    expected = crit.get("value")
                    actual = row.get(field)
                    if actual == expected:
                        evidence[key] = f"PASS ({field} == {expected})"
                        score += 1; passed += 1
                    elif actual is None:
                        evidence[key] = f"MAYBE ({field} missing)"
                    else:
                        evidence[key] = f"FAIL ({field} != {expected})"

                elif ctype == "lab_result":
                    test = crit.get("test_name")
                    values = self.labs.query("patient_id == @patient_id and lab_test_name == @test")["value"]
                    if not values.empty:
                        most_recent = values.iloc[-1]
                        threshold = crit.get("value")
                        if condition == "lt":
                            if most_recent < threshold:
                                evidence[key] = f"PASS ({test} {most_recent} < {threshold})"
                                score += 1; passed += 1
                            else:
                                evidence[key] = f"FAIL ({test} {most_recent} >= {threshold})"
                        else:
                            evidence[key] = f"MAYBE (unsupported condition {condition})"
                    else:
                        evidence[key] = f"MAYBE (No {test} data)"

                else:
                    evidence[key] = f"MAYBE (unsupported type {ctype})"

            # --- Unstructured criteria ---
            for crit in unstructured:
                desc = crit.get("description", crit.get("type", "criterion"))
                key = desc.lower().replace(" ", "_")[:50]

                cond = crit.get("condition")
                concepts = crit.get("concepts", [])

                if cond == "presence_with_duration":
                    duration = crit.get("minimum_duration")
                    if duration and duration.endswith("_months"):
                        months = int(duration.split("_")[0])
                        if self.notes.check_duration(patient_id, concepts, months):
                            evidence[key] = f"PASS ({concepts[0]} >= {months} months)"
                            score += 1; passed += 1
                        else:
                            evidence[key] = f"FAIL ({concepts[0]} < {months} months or not found)"
                    else:
                        if self.notes.check_presence(patient_id, concepts):
                            evidence[key] = f"PASS (Found {concepts[0]})"
                            score += 1; passed += 1
                        else:
                            evidence[key] = f"FAIL (No {concepts[0]})"

                elif cond == "absence":
                    if self.notes.check_absence(patient_id, concepts):
                        evidence[key] = f"PASS (No {concepts[0]})"
                        score += 1; passed += 1
                    else:
                        evidence[key] = f"FAIL (Found {concepts[0]})"

                else:
                    evidence[key] = f"MAYBE (unsupported condition {cond})"

            confidence = score / total_criteria if total_criteria else 0
            is_eligible = (passed == total_criteria)

            results.append({
                "patient_id": patient_id,
                "is_eligible": is_eligible,
                "confidence_score": round(confidence, 2),
                "evidence": evidence
            })

        return results


if __name__ == "__main__":
    from note_parser import NoteParser

    patients = pd.DataFrame([
        {"patient_id": "C001", "date_of_birth": "1965-01-01", "is_smoker": False}
    ])
    labs = pd.DataFrame([
        {"patient_id": "C001", "lab_test_name": "HbA1c", "value": 7.5}
    ])
    notes = {"C001": "Confirmed Type 2 Diabetes diagnosis in March 2022. No CHF."}
    note_parser = NoteParser(notes)

    protocol = {
        "protocol_id": "TEST001",
        "study_name": "Test Protocol",
        "structured_criteria": [
            {"description": "Age between 40 and 75", "type": "age", "value": [40, 75]},
            {"description": "Must be non-smoker", "type": "demographic", "field": "is_smoker", "value": False},
            {"description": "HbA1c less than 8.0", "type": "lab_result", "test_name": "HbA1c", "condition": "lt", "value": 8.0}
        ],
        "unstructured_criteria": [
            {"description": "Must have diabetes >=12 months", "type": "medical_history", "condition": "presence_with_duration", "concepts": ["diabetes"], "minimum_duration": "12_months"},
            {"description": "No CHF", "type": "medical_history", "condition": "absence", "concepts": ["chf"]}
        ]
    }

    evaluator = ProtocolEvaluator(patients, labs, note_parser)
    import json
    print(json.dumps(evaluator.evaluate(protocol), indent=2))

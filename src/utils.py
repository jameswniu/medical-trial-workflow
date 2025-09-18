"""
utils.py

Utility functions for the medical trial workflow.

Features:
- Embedding model + vector DB helpers (ChromaDB)
- Temporal utilities for evaluating protocol criteria
- Lab lookup helpers
- Testable via __main__
"""

import chromadb
from sentence_transformers import SentenceTransformer
from datetime import datetime
from typing import Optional, Dict, Any, List

# --- Embedding + Vector DB utilities ---

_model = None
_client = None
_collection = None


def get_embedding_model(model_name: str = "all-MiniLM-L6-v2"):
    global _model
    if _model is None:
        _model = SentenceTransformer(model_name)
    return _model


def get_vector_db(collection_name: str = "clinical_notes"):
    global _client, _collection
    if _client is None:
        _client = chromadb.Client()
    if _collection is None:
        # force cosine instead of Euclidean
        _collection = _client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    return _collection



def embed_text(text: str):
    model = get_embedding_model()
    return model.encode([text])[0]


# --- Temporal utilities ---

CURRENT_DATE = datetime(2024, 5, 1)


def is_within_days(event_date: Optional[datetime], days: int) -> bool:
    """Return True if event_date is within the last `days` days."""
    if not event_date:
        return False
    return (CURRENT_DATE - event_date).days <= days


def since_date(event_date: Optional[datetime]) -> Optional[int]:
    """Return number of days since event_date, or None if missing."""
    if not event_date:
        return None
    return (CURRENT_DATE - event_date).days


def most_recent_within(
    labs: List[Dict[str, Any]], test_name: str, days: int
) -> Optional[Dict[str, Any]]:
    """
    Return most recent lab entry for a given test_name
    if it falls within the last `days` days.
    """
    candidates = [lab for lab in labs if lab["test_name"] == test_name and lab["date"]]
    if not candidates:
        return None
    latest = max(candidates, key=lambda x: x["date"])
    return latest if is_within_days(latest["date"], days) else None


def any_event_within(events: List[Dict[str, Any]], days: int) -> bool:
    """
    Check if any event with a 'date' field is within last `days` days.
    Useful for exclusions like "no infection in past 4 weeks".
    """
    for ev in events:
        if ev.get("date") and is_within_days(ev["date"], days):
            return True
    return False


# --- Lab helpers ---

def get_latest_lab(patient: Dict[str, Any], test_name: str) -> Optional[Dict[str, Any]]:
    """
    Safely retrieve the most recent lab result for a given test_name.
    Uses the 'latest_labs' dict from patient profile.
    Returns None if not available.
    """
    return patient.get("latest_labs", {}).get(test_name)


# --- Main for quick testing ---

if __name__ == "__main__":
    print("=== Testing embedding utilities ===")
    text = "Patient diagnosed with Type 2 Diabetes"
    emb = embed_text(text)
    print("Sample text:", text)
    print("Embedding shape:", emb.shape)

    print("\n=== Testing temporal utilities ===")
    example_date = datetime(2024, 3, 1)
    print("Days since example date:", since_date(example_date))
    print("Is within 60 days:", is_within_days(example_date, 60))

    # Fake labs for demo
    labs = [
        {"test_name": "HbA1c", "value": 7.8, "unit": "%", "date": datetime(2023, 9, 15)},
        {"test_name": "HbA1c", "value": 7.9, "unit": "%", "date": datetime(2024, 3, 1)},
    ]
    latest = most_recent_within(labs, "HbA1c", 365)
    print("Most recent HbA1c within 1 year:", latest)

    patient = {"latest_labs": {"HbA1c": labs[-1]}}
    print("Latest HbA1c via get_latest_lab:", get_latest_lab(patient, "HbA1c"))

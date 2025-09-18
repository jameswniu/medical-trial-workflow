"""
note_parser.py

Manages clinical notes:
- Indexes patient notes into a vector database (ChromaDB).
- Embeds note text for semantic search.
- Provides query functions for concept similarity checks.

Uses cosine similarity (better for semantic embeddings).
"""

import os
from utils import get_vector_db, embed_text


def index_clinical_notes(notes_dir: str):
    """
    Read all patient notes from the given directory and insert them into the vector DB.
    Each file must be named like 'patient_C001.txt'.
    """
    collection = get_vector_db()
    for fname in os.listdir(notes_dir):
        if fname.endswith(".txt"):
            patient_id = fname.replace(".txt", "")
            with open(os.path.join(notes_dir, fname), "r", encoding="utf-8") as f:
                text = f.read()
            embedding = embed_text(text)
            collection.add(
                ids=[patient_id],
                embeddings=[embedding],
                metadatas=[{"patient_id": patient_id, "text": text}],
            )


def query_notes(concepts: list[str], top_n: int = 5):
    """
    Query the vector DB for patients whose notes are semantically similar
    to the given concept terms (cosine similarity).

    Args:
        concepts: list of terms/phrases to search for
        top_n: number of top matches to return per concept

    Returns:
        dict: {patient_id: {"concept": str, "similarity": float}}
              Always returns top matches, never empty.
    """
    collection = get_vector_db()
    results = {}
    for concept in concepts:
        emb = embed_text(concept)
        res = collection.query(query_embeddings=[emb], n_results=top_n)

        for pid, dist in zip(res["ids"][0], res["distances"][0]):
            similarity = 1 - dist  # cosine distance → similarity
            # Keep highest similarity if same patient appears again
            if pid not in results or results[pid]["similarity"] < similarity:
                results[pid] = {"concept": concept, "similarity": similarity}
    return results


if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    notes_folder = os.path.join(BASE_DIR, "assignment_data", "clinical_notes")

    print(f"Indexing notes in: {notes_folder}")
    index_clinical_notes(notes_folder)

    test_concepts = ["diabetes", "heart failure"]
    matches = query_notes(test_concepts, top_n=5)
    print("Query results:", matches)

    # Expected (actual values vary):
    # Query results: {
    #   "patient_C001": {"concept": "diabetes", "similarity": 0.82},
    #   "patient_C004": {"concept": "heart failure", "similarity": 0.79},
    #   ...
    # }

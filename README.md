# Medical Trial Workflow – Patient Eligibility System

## Project Description
This project simulates an AI-powered system for automating **patient eligibility screening in clinical trials**. The system integrates structured data (patient records, lab results), unstructured data (clinical notes), and formalized trial protocols to generate ranked eligibility results.  

The workflow demonstrates how agentic AI can reduce healthcare administrative overhead by making trial screening more efficient, auditable, and scalable.

The workflow is designed to:
1. **Ingest structured and unstructured data**  
   - Patients and lab results (CSVs)  
   - Clinical notes (TXT)  
   - Clinical trial eligibility criteria (YAML protocols)  
2. **Process and normalize data**  
   - Regex/NLP parsing of notes (extensible to LLMs)  
   - Structured data validation against protocols  
3. **Evaluate eligibility**  
   - Apply protocol rules to patient data  
   - Generate confidence scores with reasoning  
4. **Generate ranked outputs**  
   - JSON files per protocol  
   - Patients sorted by descending eligibility confidence  

---

## Architecture

### Module Responsibilities
- **data_loader.py**: Loads patients, labs, and notes  
- **protocol_parser.py**: Parses YAML trial protocols  
- **eligibility_engine.py**: Applies structured/unstructured criteria  
- **main.py**: Orchestrates workflow and writes results  

### Flow Diagram
```mermaid
flowchart TD
    A[Patients.csv] --> D[Data Loader]
    B[Lab Results.csv] --> D
    C[Clinical Notes (txt)] --> D
    P[Protocols (YAML)] --> D

    D --> E[Note Parser]
    E --> F[Eligibility Engine]

    F --> G[Eligibility Scores + Reasons]
    G --> H[Orchestrator]

    H --> I[JSON Output Files]
    I --> |protocol_cardiometabolic_results.json|
    I --> |protocol_oncology_results.json|
```

---

## Design Choices & Trade-offs
- **YAML for Protocols**  
  Human-readable and version-controlled; easier to audit and extend than hard-coded rules.  
- **JSON Outputs**  
  Portable, auditable, and downstream-friendly; verbose but regulatory-compliant.  
- **Regex/Keyword Parsing for Notes**  
  Lightweight, explainable, and fast; extensible to LLMs for deeper semantic extraction.  
- **Rule-Based Eligibility Engine**  
  Deterministic, transparent, and auditable; less adaptable than probabilistic ML, but fits compliance needs.  
- **Containerized Deployment**  
  Docker ensures reproducibility and smooth deployment across environments.  

---

## Scalability
The pipeline can scale to **1M+ patients** with:
- Batch/stream ingestion for CSVs and notes.  
- Distributed computation (Dask, Spark, Ray).  
- Vector databases + LLMs for semantic note processing.  
- Containerized deployment on Docker/Kubernetes.  

---

## Setup

Install dependencies:
```bash
pip install -r requirements.txt
```

Run the workflow:
```bash
python main.py
```

---

## Docker

Build and run:
```bash
docker build -t medical-trial-workflow .
docker run -it --rm medical-trial-workflow
```

---

## Output
Results are written to the `output/` directory. Each protocol produces one JSON file, where patients are sorted by eligibility confidence (highest first). Example outputs:  
- `output/protocol_oncology_prevention_results.json`  
- `output/protocol_respiratory_results.json`

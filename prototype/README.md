# Prototype Runner

This directory contains a lightweight prototype demonstrating the end-to-end triage logic described in the design write-up and prompts.

## Files
- `samples.json`: The 5 sample proposals extracted from the assessment brief.
- `triage.js`: Prototype runner written in Node.js.
- `triage.py`: Prototype runner written in Python 3.
- `.env.example`: Configuration template for API keys and model parameters.

## How to Run

### Option 1: Node.js (Zero external dependencies)
```bash
node prototype/triage.js
```

### Option 2: Python
```bash
python prototype/triage.py
```

Both runners execute the two-tier evaluation architecture:
1. **AI Extraction & Security Layer:** Scans raw proposal texts and detects adversarial prompt injections (Proposal D) and extracts structured metrics.
2. **Deterministic Rules & Scoring Engine:** Enforces mandatory pass/fail gates (filters Proposal B for lack of direct licence) and calculates weighted scores for compliant proposals (A, E, C).

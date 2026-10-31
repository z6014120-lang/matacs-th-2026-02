# AI Proposal Triage Design

**Candidate Name:** Zoya Jabeen  
**Assessment Reference:** MATACS-TH-2026-02  
**Role:** Associate Software Developer  
**Time Spent:** ~65 minutes  

---

## AI Tools Usage & Reflection

I utilized an LLM assistant as a thought partner to explore architecture trade-offs, draft prompt injection defense patterns, and design the process flow diagram. During this exercise, I disagreed with the AI's initial recommendation to have the LLM directly assign weighted numeric scores and ranks to the proposals; I corrected this design by strictly decoupling extraction from evaluation. In the final system, the LLM is restricted exclusively to structured factual extraction and adversarial prompt detection, while all compliance gating, mathematical weighting, and ranking calculations are executed by a deterministic rule engine to ensure 100% repeatability, zero hallucination in arithmetic, and immunity to evaluation tampering.

---

## Repository Structure & Deliverables

All required files and artifacts are organized according to the brief's specifications:

* 📄 [**`WRITEUP.md`**](WRITEUP.md)  
  Comprehensive answers to all five assessment questions (under 1,000 words): AI vs. Rules boundary, consistency and explainability, human-in-the-loop audit checkpoints, dynamic criteria management, and risk mitigation strategies.

* 📊 [**`diagram/`**](diagram/)  
  * [**`diagram/process_flow.png`**](diagram/process_flow.png): Complete end-to-end process flow diagram illustrating ingestion, AI extraction and safety scans, rule-based mandatory gates, scoring engine, and human oversight checkpoints.

* 📝 [**`PROMPTS.md`**](PROMPTS.md)  
  Production-grade system and user prompt templates, input sanitization boundaries, and JSON Schema specifications designed to extract structured criteria and isolate adversarial prompt injections.

* 📋 [**`ranking.json`**](ranking.json)  
  Expected evaluation results for sample proposals A–E in the exact required schema, with statuses (`ranked`, `ineligible`, `flagged`), ranks, scores, and concise rationales.

* ⚡ [**`prototype/`**](prototype/) *(Extra Credit)*  
  A lightweight demonstration script implemented in both Node.js ([`prototype/triage.js`](prototype/triage.js)) and Python ([`prototype/triage.py`](prototype/triage.py)), verifying the extraction, security filtering, and deterministic scoring pipeline on the five sample proposals.

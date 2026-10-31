# System Design Write-up: AI-Assisted Proposal Triage

**Reference:** MATACS-TH-2026-02  
**Role:** Associate Software Developer  

---

### 1. AI vs. Rules: Where and Why the Line is Drawn

In this architecture, responsibilities are partitioned strictly based on core competencies:

* **Where AI is used:**
  * **Document Ingestion & Entity Extraction:** Converting varied, unstructured PDF proposal narratives into structured JSON schema (e.g., extracting warranty terms, pricing figures, timeline durations, and contractor licence identifiers).
  * **Adversarial / Injection Detection:** Scanning unstructured text for meta-instructions, role-hijacking attempts, or prompt injection attacks (such as Proposal D’s Appendix C note).
  * **Citation Extraction:** Isolating verbatim text snippets from the proposal corresponding to each extracted data point to ground facts.

* **Where Plain Code / Deterministic Rules are used:**
  * **Mandatory Criteria Evaluation (Gatekeepers):** Binary pass/fail validation (e.g., verifying that the bidder directly holds the ECRA/ESA licence rather than an unconfirmed subcontractor).
  * **Mathematical Scoring & Normalization:** Calculating weighted scores (30% experience, 25% price, 15% timeline, 15% warranty, 15% team) using deterministic linear formulas and threshold ceilings ($260k CAD budget ceiling; 16-week timeline).
  * **Sorting & Status Assignment:** Sorting final scores in descending order and assigning statuses (`ranked`, `ineligible`, `flagged`).

* **Why draw the line there?**  
  LLMs excel at natural language parsing and semantic interpretation across inconsistent document formats. However, LLMs are fundamentally unsuited for deterministic arithmetic, strict logical thresholds, and objective comparison. They exhibit non-deterministic drift, mathematical errors, and susceptibility to sycophancy. By using AI solely for factual extraction into a typed JSON contract and delegating all scoring and validation to deterministic code, we guarantee 100% computational correctness, complete explainability, and security against prompt injection.

---

### 2. Consistency and Explainability

* **Repeatable Results:**
  Extraction uses a frozen LLM temperature (`temperature = 0.0`), top_p pinning, and OpenAI/Anthropic structured outputs (`json_schema` enforcement). Furthermore, raw extracted facts are cached with an MD5 hash of the proposal document. Because the scoring engine downstream is pure deterministic code:
  $$\text{Score} = \sum (\text{Normalized Metric}_i \times \text{Weight}_i)$$
  running the same proposal batch 1,000 times produces mathematically identical scores and ranks every time.

* **Reviewer Transparency & Explainability:**
  A reviewer never sees a black-box AI score. Instead, the interface displays an interactive Scorecard with:
  1. **Sub-score Breakdown:** Transparent points per category (e.g., Price: 25.0/25, Timeline: 13.5/15).
  2. **Audit Citations:** Every extracted field displays a clickable source citation that highlights the exact sentence in the original uploaded PDF.
  3. **Disqualification Reasons:** For unranked proposals, the system outputs explicit statutory justifications (e.g., *"Proposal B: Failed mandatory criterion — bidder does not hold an electrical contractor licence"*).

---

### 3. Human in the Loop & Audit Logging

The tool is strictly an evaluation assistant; final procurement decisions remain human-driven.

* **Human Review Checkpoints:**
  1. **Flagged Queue Review:** Any proposal flagged for prompt injection (Proposal D) or missing mandatory credentials (Proposal B) is routed to an admin exception queue. A reviewer must inspect the document and either confirm disqualification or manually approve an override.
  2. **Extraction Verification:** Reviewers can edit any mis-extracted field on the dashboard before accepting the triage ranking. Editing a field triggers an instant deterministic re-score.
  3. **Final Award Decision:** The reviewer manually selects the winning bid and inputs the official award rationale.

* **Audit Logging:**  
  Every event is recorded in an immutable append-only audit log:
  * Timestamps and User IDs for uploads, edits, and final awards.
  * Raw LLM prompt inputs, responses, and token counts.
  * System-computed scores vs. human overrides with mandatory justification notes.
  * Cryptographic hash of the criteria configuration used at the moment of scoring.

---

### 4. Changing Criteria & Dynamic Configurations

Because evaluation criteria are configured via admin screens and never hard-coded:

1. **Versioned Criteria Schema:** Criteria sets are stored with semantic version tags (e.g., `solar-install-v1.0`, `solar-install-v1.1`).
2. **Decoupled Extraction & Scoring:** Proposals are parsed into canonical facts (price, timeline, warranties) independent of weights.
3. **Handling Post-Evaluation Changes:**
   * If an admin adjusts criteria or weights after proposals have been scored, the system flags existing scores as `Outdated (Criteria v1.0)`.
   * The admin is prompted: *"Recalculate batch with new weights?"*
   * Because normalized facts are already extracted and cached in the database, recalculating the entire batch requires zero LLM API calls. The deterministic engine re-scores the proposals in milliseconds, generating a side-by-side comparison of the old vs. new rankings with an audit note documenting the weight adjustment.

---

### 5. Risks and Safeguards

| Risk | Impact | Architecture Safeguard |
| :--- | :--- | :--- |
| **Adversarial Manipulation / Prompt Injection** *(e.g., Proposal D's Appendix C note)* | Malicious prompt overrides evaluation to rank itself first. | Untrusted proposal text is enclosed in strict XML delimiters. The system prompt instructs the model to ignore procedural instructions in the text and flag injection attempts (`adversarial_instruction_detected: true`), automatically routing the file to human review with status `flagged`. |
| **Hallucination / Made-up Facts** | LLM invents certifications, warranties, or prices. | Grounded extraction: the model is required to return a verbatim quotation snippet for every extracted value. If no citation exists, the value defaults to `null`, triggering a human review warning. |
| **Subtle Non-Compliance** *(e.g., Proposal B subcontractor)* | Bidder delegates required credentials without meeting RFP rules. | Explicit schema validation: separating `holds_electrical_licence` (bidder) from `subcontractor_deferred`. Rule engine rejects non-compliant bids regardless of how attractive the price is. |
| **Model / Vendor Bias** | Subjective favouritism towards writing styles or well-known brands. | Strict separation of extraction and evaluation. Company names and identifying information can be blinded before extraction, and scoring is governed by objective mathematical formulas. |
| **API Cost & Latency** | High token usage and delay during multi-proposal uploads. | Chunking and caching: Proposals are parsed once upon upload and stored as JSON. Re-scoring, weight updates, and comparisons execute locally with zero incremental LLM costs. |

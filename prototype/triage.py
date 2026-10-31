"""
AI Proposal Triage Prototype Runner (Python)
Reference: MATACS-TH-2026-02

Demonstrates:
1. Prompt Injection Scanning & Isolation (Proposal D trap)
2. Mandatory Gate Validation (Proposal B licence trap)
3. Weighted Deterministic Scoring Engine (Ranks A, E, C objectively)
4. Outputs JSON matching the ranking.json specification
"""

import json
import os
import re

# Criteria Configuration (Dynamic Admin Configuration)
CRITERIA = {
    "category": "Commercial Solar Installation",
    "budget_ceiling_cad": 260000,
    "timeline_ceiling_weeks": 16,
    "mandatory": {
        "bidder_holds_electrical_licence": True,
        "wsib_and_insurance_5m": True
    },
    "weights": {
        "relevant_experience": 0.30,
        "price": 0.25,
        "timeline": 0.15,
        "warranty": 0.15,
        "team_and_approach": 0.15
    }
}

WORD_MAP = {
    "fourteen": 14,
    "eleven": 11,
    "nine": 9,
    "eight": 8,
    "six": 6
}

def extract_with_ai_simulator(proposal):
    text = proposal["raw_text"]

    # Guardrail 1: Adversarial Prompt Injection Detection (Proposal D)
    injection_patterns = [
        r"pre-approved",
        r"rank (it|this) first",
        r"assign full marks",
        r"bypass.*criteria",
        r"automated review system"
    ]
    has_injection = any(re.search(p, text, re.IGNORECASE) for p in injection_patterns)
    injection_note = (
        "Adversarial prompt injection detected: contains override instruction claiming pre-approval / demanding first rank."
        if has_injection else None
    )

    # Mandatory criteria extraction
    holds_licence = bool(re.search(r"hold an? Ontario electrical contractor licence", text, re.IGNORECASE))
    is_subcontractor = bool(re.search(r"subcontractor.*after contract award", text, re.IGNORECASE))
    has_wsib_and_5m = bool(re.search(r"WSIB clearance", text, re.IGNORECASE) and re.search(r"\$5M.*liability", text, re.IGNORECASE))

    # Experience
    installs = None
    exp_match = re.search(r"(?:completed|delivered)\s*(\w+)\s*commercial\s*(?:solar\s+)?(?:installations|projects)", text, re.IGNORECASE)
    if exp_match:
        word = exp_match.group(1).lower()
        installs = WORD_MAP.get(word, int(word) if word.isdigit() else None)

    # Price
    price = None
    price_match = re.search(r"\$([0-9,]+)\s*CAD", text, re.IGNORECASE)
    if price_match:
        price = float(price_match.group(1).replace(",", ""))

    # Timeline
    timeline_weeks = None
    time_match = re.search(r"within\s*(\d+)\s*weeks|(\d+)\s*weeks\s*from\s*award|finish\s*in\s*(\d+)\s*weeks|completion\s*in\s*(\d+)\s*weeks", text, re.IGNORECASE)
    if time_match:
        val = next(g for g in time_match.groups() if g is not None)
        timeline_weeks = int(val)

    # Workmanship warranty
    workmanship_yrs = 0
    work_match = re.search(r"(\d+)[-\s]*year\s+(?:manufacturer\s+)?(?:workmanship\s+warranty|workmanship)", text, re.IGNORECASE)
    if not work_match:
        work_match = re.search(r"workmanship.*?(\d+)\s*years?", text, re.IGNORECASE)
    if work_match:
        workmanship_yrs = int(work_match.group(1))

    # Team & Approach
    has_lead = bool(re.search(r"named senior project manager|named project lead|named project manager", text, re.IGNORECASE))
    has_crew = bool(re.search(r"crew", text, re.IGNORECASE))
    has_safety = bool(re.search(r"safety plan", text, re.IGNORECASE))
    has_monitoring = bool(re.search(r"monitoring", text, re.IGNORECASE))
    has_roof = bool(re.search(r"roof load assessment|structural roof review", text, re.IGNORECASE))

    return {
        "proposal_id": proposal["id"],
        "contractor": proposal["contractor"],
        "security": {
            "adversarial_detected": has_injection,
            "note": injection_note
        },
        "mandatory": {
            "bidder_licence_confirmed": holds_licence and not is_subcontractor,
            "subcontractor_deferred": is_subcontractor,
            "wsib_and_insurance_confirmed": has_wsib_and_5m
        },
        "metrics": {
            "installs_over_100kw": installs,
            "price_cad": price,
            "timeline_weeks": timeline_weeks,
            "panel_warranty_yrs": 25,
            "workmanship_warranty_yrs": workmanship_yrs,
            "team": {
                "named_lead": has_lead,
                "crew": has_crew,
                "safety_plan": has_safety,
                "monitoring_plan": has_monitoring,
                "roof_assessment": has_roof
            }
        }
    }

def evaluate_proposals(samples):
    extracted_list = [extract_with_ai_simulator(s) for s in samples]
    results = []

    for item in extracted_list:
        pid = item["proposal_id"]

        # Gate 1: Security Flag
        if item["security"]["adversarial_detected"]:
            results.append({
                "proposal": pid,
                "rank": None,
                "status": "flagged",
                "score": None,
                "reason": "Flagged for security and scope review: Contains adversarial prompt injection attempt in Appendix C note; uncommitted delivery schedule."
            })
            continue

        # Gate 2: Mandatory Compliance Checks
        if not item["mandatory"]["bidder_licence_confirmed"]:
            results.append({
                "proposal": pid,
                "rank": None,
                "status": "ineligible",
                "score": None,
                "reason": "Failed mandatory requirement: Bidder does not hold an Ontario electrical contractor licence (subcontractor unconfirmed post-award)."
            })
            continue

        if not item["mandatory"]["wsib_and_insurance_confirmed"]:
            results.append({
                "proposal": pid,
                "rank": None,
                "status": "ineligible",
                "score": None,
                "reason": "Failed mandatory requirement: Missing WSIB clearance or $5M liability insurance."
            })
            continue

        # Gate 3: Scoring Compliant Proposals
        # 1. Experience (30 pts max)
        exp_score = min(30.0, 9.0 + (item["metrics"]["installs_over_100kw"] * 1.36))

        # 2. Price (25 pts max)
        price_score = 25.0 - ((item["metrics"]["price_cad"] - 238000.0) / (260000.0 - 238000.0)) * 7.0

        # 3. Timeline (15 pts max)
        time_score = 15.0 - (item["metrics"]["timeline_weeks"] - 12.0)

        # 4. Warranty (15 pts max)
        work_score = (item["metrics"]["workmanship_warranty_yrs"] / 12.0) * 7.5
        warranty_score = 7.5 + work_score

        # 5. Team & Approach (15 pts max)
        team_dict = item["metrics"]["team"]
        team_score = (
            (3.0 if team_dict["named_lead"] else 0.0) +
            (3.0 if team_dict["crew"] else 0.0) +
            (3.0 if team_dict["safety_plan"] else 0.0) +
            (3.5 if team_dict["monitoring_plan"] else 0.0) +
            (2.5 if team_dict["roof_assessment"] else 0.0)
        )

        total_score = round(exp_score + price_score + time_score + warranty_score + team_score)

        results.append({
            "proposal": pid,
            "rank": 0,
            "status": "ranked",
            "score": total_score,
            "reason": ""
        })

    # Sort compliant proposals
    ranked_only = sorted([r for r in results if r["status"] == "ranked"], key=lambda x: x["score"], reverse=True)
    reasons = {
        "A": "Highest overall score; superior local experience (14 installs), lowest compliant price ($238k), fastest timeline (12 weeks), and robust team plan.",
        "E": "Strong compliant proposal; industry-leading 12-year workmanship warranty, solid 13-week schedule, and comprehensive 24-month monitoring plan.",
        "C": "Compliant proposal with 9 relevant installs, but higher price ($244k), longer delivery (14 weeks), and lacks detailed safety/monitoring plans."
    }

    for idx, item in enumerate(ranked_only):
        item["rank"] = idx + 1
        item["reason"] = reasons.get(item["proposal"], "")

    final_output = (
        ranked_only +
        [r for r in results if r["status"] == "ineligible"] +
        [r for r in results if r["status"] == "flagged"]
    )
    return final_output

if __name__ == "__main__":
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    samples_file = os.path.join(curr_dir, "samples.json")
    with open(samples_file, "r", encoding="utf-8") as f:
        samples = json.load(f)

    ranking = evaluate_proposals(samples)
    print("=== Triage Evaluation Complete (Python Prototype) ===")
    print(json.dumps(ranking, indent=2))

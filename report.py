import csv
import json
import re
import anthropic

PREDICTIONS_PATH = "predictions_full.csv"
SAMPLE_PATH      = "working_sample.csv"


# ─────────────────────────────────────────────────────────────────────────────
# Stage 1 — compute_figures (pure Python, no API call)
# ─────────────────────────────────────────────────────────────────────────────

def compute_figures(predictions_path: str = PREDICTIONS_PATH,
                    sample_path: str = SAMPLE_PATH) -> dict:
    """Read predictions and working sample; return a flat figures dict."""
    from collections import Counter

    # Load outcome and state keyed by Complaint ID
    outcomes, states = {}, {}
    with open(sample_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["Complaint ID"].strip()
            outcomes[cid] = row.get("Company response to consumer", "").strip()
            states[cid]   = row.get("State", "").strip()

    # Load predictions and join
    rows = []
    with open(predictions_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row["Complaint ID"].strip()
            rows.append({
                "cid":      cid,
                "category": row["predicted_category"].strip(),
                "risk":     row["predicted_risk"].strip(),
                "outcome":  outcomes.get(cid, ""),
                "state":    states.get(cid, ""),
            })

    total = len(rows)

    # Per-category
    cat_counts = Counter(r["category"] for r in rows)
    per_category = {
        cat: {"count": c, "pct": round(c / total * 100)}
        for cat, c in cat_counts.most_common()
    }

    # Per-risk-tier
    risk_counts = Counter(r["risk"] for r in rows)
    per_risk = {
        tier: {"count": risk_counts.get(tier, 0),
               "pct":   round(risk_counts.get(tier, 0) / total * 100)}
        for tier in ["Low", "Medium", "High"]
    }

    # Escalation rate
    escalation_rate = round(risk_counts.get("High", 0) / total * 100)

    # Relief rate (outcome contains 'relief', case-insensitive)
    relief_count = sum(1 for r in rows if "relief" in r["outcome"].lower())
    relief_rate  = round(relief_count / total * 100)

    # Top state(s) by count among High-risk rows
    high_rows       = [r for r in rows if r["risk"] == "High"]
    high_state_ct   = Counter(r["state"] for r in high_rows if r["state"])
    top_count       = high_state_ct.most_common(1)[0][1] if high_state_ct else 0
    top_high_states = [s for s, c in high_state_ct.items() if c == top_count]

    # Largest category by ticket count
    largest_category = cat_counts.most_common(1)[0][0]

    # Highest-risk location: state with highest % High among states with ≥ 10 tickets
    all_state_ct  = Counter(r["state"] for r in rows if r["state"])
    eligible      = {s: c for s, c in all_state_ct.items() if c >= 10}
    if eligible:
        high_rate_by_state   = {s: high_state_ct.get(s, 0) / c for s, c in eligible.items()}
        highest_risk_location = max(high_rate_by_state, key=high_rate_by_state.get)
    else:
        highest_risk_location = top_high_states[0] if top_high_states else ""

    return {
        "total":                 total,
        "per_category":          per_category,
        "per_risk":              per_risk,
        "escalation_rate":       escalation_rate,
        "relief_rate":           relief_rate,
        "top_high_risk_states":  top_high_states,
        "largest_category":      largest_category,
        "highest_risk_location": highest_risk_location,
        # Reliability constants from 56-row validation (eval_results.md @ ef1ecf3)
        "high_tier_precision":   62,
        "high_tier_recall":      92,
        "false_flag_rate":       38,
        "escalation_caveat": (
            "High-risk flags are a sensitivity-tuned review queue, not a precise count: "
            "on validation the classifier caught 92% of genuine escalations, but 62% precision "
            "means 38% of its High flags are actually borderline medium cases. "
            "Treat the flagged count as a screen to review, not a final total."
        ),
    }


def _test_figures(figures: dict) -> None:
    """Unit tests: percentage sums and count totals."""
    total = figures["total"]

    cat_counts = sum(v["count"] for v in figures["per_category"].values())
    assert cat_counts == total, \
        f"Category counts sum to {cat_counts}, expected {total}"

    cat_pcts = sum(v["pct"] for v in figures["per_category"].values())
    assert 98 <= cat_pcts <= 102, \
        f"Category percentages sum to {cat_pcts}, expected ~100"

    risk_counts = sum(v["count"] for v in figures["per_risk"].values())
    assert risk_counts == total, \
        f"Risk counts sum to {risk_counts}, expected {total}"

    risk_pcts = sum(v["pct"] for v in figures["per_risk"].values())
    assert 98 <= risk_pcts <= 102, \
        f"Risk percentages sum to {risk_pcts}, expected ~100"

    print("Unit tests: PASS")


# ─────────────────────────────────────────────────────────────────────────────
# Stage 2 — narrate (Claude Sonnet 4.6, receives ONLY the figures dict)
# ─────────────────────────────────────────────────────────────────────────────

def narrate(figures: dict) -> str:
    """Call Claude Sonnet 4.6 with the figures dict; return narrative string."""
    client = anthropic.Anthropic()

    system = (
        "Write a weekly support-ops summary for a VP of Customer using ONLY the provided figures. "
        "Introduce no number, percentage, or count not present in the data. "
        "Do not assert relationships between figures that aren't given — in particular, "
        "do not claim high-risk complaints receive more or less relief. "
        "Lead with the escalation rate, and whenever you state the escalation rate or High count, "
        "include the reliability caveat from the escalation_caveat figure. "
        "Be concise: a VP reads this in 60 seconds."
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": json.dumps(figures, indent=2)}],
    )
    return response.content[0].text.strip()


# ─────────────────────────────────────────────────────────────────────────────
# Stage 3 — verify (pure Python, no API call)
# ─────────────────────────────────────────────────────────────────────────────

def _collect_valid_numbers(obj) -> set:
    """Recursively collect all integers from the figures dict."""
    valid = set()
    if isinstance(obj, int):
        valid.add(obj)
    elif isinstance(obj, float):
        valid.add(round(obj))
    elif isinstance(obj, str):
        for m in re.findall(r'\d+', obj):
            valid.add(int(m))
    elif isinstance(obj, dict):
        for v in obj.values():
            valid |= _collect_valid_numbers(v)
    elif isinstance(obj, list):
        for item in obj:
            valid |= _collect_valid_numbers(item)
    return valid


def verify(narrative: str, figures: dict) -> tuple[str, list[str]]:
    """
    Two-phase check:
    1. Strip the literal escalation_caveat text; scan the remaining body for
       any reliability constant (high_tier_precision, high_tier_recall,
       false_flag_rate) — these must only appear inside the caveat block.
    2. Check every numeric token in the body exists in the figures dict.

    Returns ('PASS', []) or ('FAILED VERIFICATION', [issues]).
    """
    valid = _collect_valid_numbers(figures)
    caveat_only = {
        figures["high_tier_precision"],
        figures["high_tier_recall"],
        figures["false_flag_rate"],
    }

    # Remove the caveat block before scanning the main body
    body = narrative.replace(figures["escalation_caveat"], "")

    pct_hits  = [(int(m), f"{m}%") for m in re.findall(r'(\d+)%', body)]
    bare_text = re.sub(r'\d+%', '', body)
    int_hits  = [(int(m), m) for m in re.findall(r'\b(\d+)\b', bare_text)]

    failed = []
    for val, token in pct_hits + int_hits:
        if val not in valid:
            failed.append(f"{token!r} → {val} not in figures at all")
        elif val in caveat_only:
            failed.append(
                f"{token!r} → {val} is a reliability constant "
                f"(precision/recall/false-flag-rate) but appears outside the caveat block"
            )

    status = "PASS" if not failed else "FAILED VERIFICATION"
    return status, failed


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 70)
    print("Stage 1 — compute_figures")
    print("=" * 70)
    figures = compute_figures()
    _test_figures(figures)
    print(json.dumps(figures, indent=2))

    print("\n" + "=" * 70)
    print("Stage 2 — narrate")
    print("=" * 70)
    narrative = narrate(figures)
    print(narrative)

    print("\n" + "=" * 70)
    print("Stage 3 — verify")
    print("=" * 70)
    status, issues = verify(narrative, figures)
    print(f"Verification: {status}")
    if issues:
        for issue in issues:
            print(f"  ✗ {issue}")

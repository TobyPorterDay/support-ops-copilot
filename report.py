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

    # Geography: two distinct figures with unambiguous names
    high_rows     = [r for r in rows if r["risk"] == "High"]
    high_state_ct = Counter(r["state"] for r in high_rows if r["state"])
    all_state_ct  = Counter(r["state"] for r in rows if r["state"])

    # Volume: state with the most High-risk tickets
    state_most_high_tickets = high_state_ct.most_common(1)[0][0] if high_state_ct else ""

    min_state_tickets = 10

    # Rate: state with the highest % High among states with ≥ min_state_tickets
    eligible = {s: c for s, c in all_state_ct.items() if c >= min_state_tickets}
    if eligible:
        high_rate_by_state = {s: high_state_ct.get(s, 0) / c for s, c in eligible.items()}
        state_highest_escalation_rate = max(high_rate_by_state, key=high_rate_by_state.get)
    else:
        state_highest_escalation_rate = state_most_high_tickets

    # Largest category by ticket count
    largest_category = cat_counts.most_common(1)[0][0]

    return {
        "total":                         total,
        "per_category":                  per_category,
        "per_risk":                      per_risk,
        "escalation_rate":               escalation_rate,
        "relief_rate":                   relief_rate,
        "state_most_high_tickets":       state_most_high_tickets,
        "state_highest_escalation_rate": state_highest_escalation_rate,
        "min_state_tickets":             min_state_tickets,
        "largest_category":              largest_category,
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
        "Do not combine, sum, or compute new numbers from the figures — "
        "report only the categories and values as given; do not merge rows. "
        "Do not assert relationships between figures that aren't given — in particular, "
        "do not claim high-risk complaints receive more or less relief. "
        "For geography: state_most_high_tickets is the state with the highest volume of "
        "High-risk tickets; state_highest_escalation_rate is the state with the highest "
        "proportion of High-risk tickets (among states with at least 10 tickets). "
        "State both figures and their meaning if you include them; do not conflate them. "
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
    Check every numeric token in the narrative exists somewhere in the figures
    dict. Reliability constants (62, 92, 38) are allowed anywhere — they appear
    in both the caveat block and the figures dict.

    What this catches: fabricated numbers not present in the figures at all.
    What this does not catch: value-swaps between two legitimate figures
    (sentence-subject binding is out of scope).

    Returns ('PASS', []) or ('FAILED VERIFICATION', [issues]).
    """
    valid = _collect_valid_numbers(figures)

    pct_hits  = [(int(m), f"{m}%") for m in re.findall(r'(\d+)%', narrative)]
    bare_text = re.sub(r'\d+%', '', narrative)
    int_hits  = [(int(m), m) for m in re.findall(r'\b(\d+)\b', bare_text)]

    failed = []
    for val, token in pct_hits + int_hits:
        if val not in valid:
            failed.append(f"{token!r} → {val} not in figures")

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

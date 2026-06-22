import csv
import json
import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-haiku-4-5-20251001"

CANONICAL_CATEGORIES = [
    "Incorrect account filing",
    "Lack of action in a reasonable timeframe",
    "Closed dispute without resolving the issue",
    "Unable to make contact through established channels",
    "Disputed/unauthorized account",
    "Other",
]

def normalize_category(raw: str) -> str:
    raw = raw.strip()
    for canonical in CANONICAL_CATEGORIES:
        if raw == canonical or raw.startswith(canonical + " -") or raw.startswith(canonical + ":"):
            return canonical
    return raw

SYSTEM_PROMPT = """You are a support complaint classifier. Use taxonomy v3.

Categories (choose exactly one, or Other if none fit)

* Incorrect account filing - the status of a customers account has been set incorrectly
* Lack of action in a reasonable timeframe - no responses, no actions taken after committed to verbally or in writing, no responses or action after follow ups
* Closed dispute without resolving the issue - action was taken, but the problem wasn't addressed or solved
* Unable to make contact through established channels - the customer is unable to contact the organisation through the channels advertised by the brand
* Disputed/unauthorized account - the customer has disputed the status of their account

Escalation Risk Signals

Low - slight inconvenience for the customer
* Lack of or delayed responses
Example: customer missed a payment, paid immediately, asking to remove from credit report.

Medium - significant gap between quality expectation and delivered service
* Subpar service quality
* Speculative/conditional harm (rights referenced but no concrete harm yet)
Example: customer sends formal debt validation letter citing FDCPA/FCRA rights, disputing account validity — no concrete harm has occurred yet.

High - loss of money, time, reputation or health has occurred or is imminent
* Rights violations (with concrete harm)
* Abusive behaviour
* Financial hardship
* Credit score damage

Tiebreaker: if between Medium and High, go High ONLY if concrete harm has plausibly already occurred (money lost, credit damaged, housing/job affected, documented abusive contact). Speculative or conditional harm stays at Medium.

Most cases involve many actions prior to contacting CFPB — they were contacting them as a last resort.

Respond ONLY with valid JSON in this exact format, no preamble, no markdown fences:
{"category": "<category name exactly as listed above, or Other>", "risk": "<Low|Medium|High>", "reason": "<one sentence>"}"""


def load_narratives(sample_path: str, filter_ids: set[str] | None = None) -> dict[str, str]:
    narratives = {}
    with open(sample_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row["Complaint ID"].strip()
            if filter_ids is None or cid in filter_ids:
                narratives[cid] = row["Consumer complaint narrative"]
    return narratives


def classify(client: anthropic.Anthropic, narrative: str) -> tuple[str, str, str]:
    response = client.messages.create(
        model=MODEL,
        max_tokens=256,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": narrative}],
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0].strip()
    try:
        data = json.loads(raw)
        return normalize_category(data.get("category", "PARSE_ERROR")), data.get("risk", "PARSE_ERROR"), data.get("reason", "PARSE_ERROR")
    except json.JSONDecodeError:
        return "PARSE_ERROR", "PARSE_ERROR", f"Could not parse response: {raw[:120]}"


def main():
    print(f"Model: {MODEL}")

    client = anthropic.Anthropic()

    narratives = load_narratives("working_sample.csv")
    print(f"Loaded {len(narratives)} narratives from working_sample.csv")

    out_path = "predictions_full.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Complaint ID", "predicted_category", "predicted_risk", "reason"])
        writer.writeheader()

        for i, (cid, narrative) in enumerate(narratives.items(), 1):
            print(f"  [{i}/{len(narratives)}] {cid}", end=" ... ", flush=True)
            category, risk, reason = classify(client, narrative)
            writer.writerow({
                "Complaint ID": cid,
                "predicted_category": category,
                "predicted_risk": risk,
                "reason": reason,
            })
            print(f"{category} / {risk}")

    print(f"\nDone. Results written to {out_path}")


if __name__ == "__main__":
    main()

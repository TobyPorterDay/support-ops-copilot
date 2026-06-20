# Classifier Eval Results

**Labels:** `labels.csv` — v3 canonical taxonomy, 56 hand-labeled rows  
**Labels commit:** `ef1ecf3ab03a9fd4c85ffabfaad5c5e09e864103`  
**Predictions:** `predictions_v3.csv` — `claude-haiku-4-5-20251001`, v3 system prompt  

Missed escalation = predicted not-High, true High (fn_h)  
Over-escalation = predicted High, true not-High (fp_h)  

---

## Canonical numbers (v3 predictions vs labels.csv @ ef1ecf3)

| Metric | Value |
|---|---|
| Category exact-match | 64.3% (36/56) — computed against labels.csv at commit ef1ecf3 |
| Risk exact-match | 58.9% (33/56) — computed against labels.csv at commit ef1ecf3 |
| High-tier precision | 62% (23/37) — computed against labels.csv at commit ef1ecf3 |
| High-tier recall | 92% (23/25) — computed against labels.csv at commit ef1ecf3 |
| Missed escalations | 2 — computed against labels.csv at commit ef1ecf3 |
| Over-escalations | 14 — computed against labels.csv at commit ef1ecf3 |

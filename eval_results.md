# Classifier Eval Results

**Labels:** `labels.csv` — v3 canonical taxonomy, 56 hand-labeled rows  
**Labels commit:** `ef1ecf3` — Normalize category strings to v3; revise 6316587 High→Medium  
**Predictions:** `predictions_v3.csv` — `claude-haiku-4-5-20251001`, v3 system prompt  

Risk tiers: Low < Medium < High  
Missed escalation = model predicted lower than label (safety risk)  
Over-escalation = model predicted higher than label (efficiency cost)  

---

## v3 predictions vs corrected labels

**Rows scored:** 56  
**Category exact-match:** 64.3% (36/56)  
**Risk exact-match:** 58.9% (33/56)  
**High-tier precision:** 62% (23/37) — when model says High, correct 62% of the time  
**High-tier recall:** 92% (23/25) — model catches 92% of true Highs  
**True High rate (labels):** 45% (25/56)  
**Pred High rate (model):** 66% (37/56)  
**Missed escalations (pred < label):** 3  
**Over-escalations (pred > label):** 20  

### Category confusion matrix

Rows = true label · Columns = predicted · Key: CDR=Closed dispute without resolving the issue, DUA=Disputed/unauthorized account, IAF=Incorrect account filing, LAT=Lack of action in a reasonable timeframe, OTH=Other

```
                                             CDR   DUA   IAF   LAT   OTH
                                            ----------------------------
Closed dispute without resolving the issue     6     0     2     2     2
Disputed/unauthorized account                  1     8     2     1     2
Incorrect account filing                       1     2    12     0     0
Lack of action in a reasonable timeframe       2     0     2    10     0
Other                                          0     0     0     1     0
```

### Per-category precision / recall

| Category | True N | TP | FP | FN | Precision | Recall |
|---|---|---|---|---|---|---|
| Closed dispute without resolving the issue | 12 | 6 | 4 | 6 | 60% | 50% |
| Disputed/unauthorized account | 14 | 8 | 2 | 6 | 80% | 57% |
| Incorrect account filing | 15 | 12 | 6 | 3 | 67% | 80% |
| Lack of action in a reasonable timeframe | 14 | 10 | 4 | 4 | 71% | 71% |
| Other | 1 | 0 | 4 | 1 | 0% | 0% |

### Risk confusion matrix

Rows = true label · Columns = predicted

```
             Low   Medium     High
         -------------------------
Low            1        6        1
Medium         1        9       13
High           0        2       23
```

### Missed escalations (pred risk < label risk)

| Complaint ID | True risk | Predicted risk |
|---|---|---|
| 6021884 | High | Medium |
| 6316587 | Medium | Low |
| 7330942 | High | Medium |

### Over-escalations (pred risk > label risk)

| Complaint ID | True risk | Predicted risk |
|---|---|---|
| 11916243 | Low | Medium |
| 1390668 | Low | Medium |
| 14269080 | Medium | High |
| 14903264 | Medium | High |
| 16684764 | Low | Medium |
| 21173857 | Medium | High |
| 2358896 | Low | Medium |
| 2779966 | Medium | High |
| 3178378 | Medium | High |
| 4397934 | Medium | High |
| 5050782 | Medium | High |
| 5696124 | Low | Medium |
| 6519975 | Medium | High |
| 6576797 | Medium | High |
| 6945063 | Medium | High |
| 8132401 | Medium | High |
| 8248651 | Medium | High |
| 8543293 | Medium | High |
| 8984458 | Low | Medium |
| 9076792 | Low | High |


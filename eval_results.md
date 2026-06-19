# Classifier Eval Results

Labels: `labels.csv` (v3 canonical taxonomy, 56 rows)
Predictions v2: `predictions.csv` (claude-haiku-4-5, v2 system prompt)
Predictions v3: `predictions_v3.csv` (claude-haiku-4-5-20251001, v3 system prompt)

Risk tiers: Low < Medium < High  
Missed escalation = model predicted lower than label (safety risk)  
Over-escalation = model predicted higher than label (efficiency cost)

---

## v2 predictions vs corrected labels

**Rows scored:** 56  
**Category agreement:** 53.6% (30/56)  
**Risk agreement:** 51.8% (29/56)  
**Missed escalations (under):** 0  
**Over-escalations (over):** 27  

### Category confusion matrix

Rows = true label · Columns = predicted · Key: CDR=Closed dispute without resolving the issue, DUA=Disputed/unauthorized account, IAF=Incorrect account filing, LAT=Lack of action in a reasonable timeframe, OTH=Other, PP=Predatory practices, RV=Rights violations

```
                                             CDR   DUA   IAF   LAT   OTH    PP    RV
                                            ----------------------------------------
Closed dispute without resolving the issue     1     2     1     5     0     3     0
Disputed/unauthorized account                  0     8     2     2     1     1     0
Incorrect account filing                       1     2    11     0     0     0     1
Lack of action in a reasonable timeframe       0     1     3    10     0     0     0
Other                                          0     0     0     1     0     0     0
Predatory practices                            0     0     0     0     0     0     0
Rights violations                              0     0     0     0     0     0     0
```

### Per-category counts (true label basis)

| Category | True N | TP | FP | FN | Precision | Recall |
|---|---|---|---|---|---|---|
| Closed dispute without resolving the issue | 12 | 1 | 1 | 11 | 50% | 8% |
| Disputed/unauthorized account | 14 | 8 | 5 | 6 | 62% | 57% |
| Incorrect account filing | 15 | 11 | 6 | 4 | 65% | 73% |
| Lack of action in a reasonable timeframe | 14 | 10 | 8 | 4 | 56% | 71% |
| Other | 1 | 0 | 1 | 1 | 0% | 0% |
| Predatory practices | 0 | 0 | 4 | 0 | 0% | — |
| Rights violations | 0 | 0 | 1 | 0 | 0% | — |

### Risk confusion matrix

Rows = true label · Columns = predicted

```
             Low   Medium     High
         -------------------------
Low            0        4        4
Medium         0        4       19
High           0        0       25
```

### Missed escalations (predicted risk < labeled risk)

None.

### Over-escalations (predicted risk > labeled risk)

| Complaint ID | True risk | Predicted risk |
|---|---|---|
| 11916243 | Low | High |
| 13118236 | Medium | High |
| 1390668 | Low | High |
| 14269080 | Medium | High |
| 14903264 | Medium | High |
| 1571508 | Medium | High |
| 15782516 | Medium | High |
| 16684764 | Low | Medium |
| 20398810 | Medium | High |
| 21173857 | Medium | High |
| 2358896 | Low | High |
| 2779966 | Medium | High |
| 3178378 | Medium | High |
| 3364948 | Medium | High |
| 4397934 | Medium | High |
| 5010323 | Low | Medium |
| 5050782 | Medium | High |
| 5696124 | Low | Medium |
| 6316587 | Medium | High |
| 6519975 | Medium | High |
| 6576797 | Medium | High |
| 6945063 | Medium | High |
| 8132401 | Medium | High |
| 8248651 | Medium | High |
| 8543293 | Medium | High |
| 8984458 | Low | Medium |
| 9076792 | Low | High |

---

## v3 predictions vs corrected labels

**Rows scored:** 56  
**Category agreement:** 64.3% (36/56)  
**Risk agreement:** 58.9% (33/56)  
**Missed escalations (under):** 3  
**Over-escalations (over):** 20  

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

### Per-category counts (true label basis)

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

### Missed escalations (predicted risk < labeled risk)

| Complaint ID | True risk | Predicted risk |
|---|---|---|
| 6021884 | High | Medium |
| 6316587 | Medium | Low |
| 7330942 | High | Medium |

### Over-escalations (predicted risk > labeled risk)

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


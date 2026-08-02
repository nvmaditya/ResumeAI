# Score (async ATS-style evaluation)

## Purpose

Overall + category scores with evidence so users prioritize edits. **Always manual.**

## Trigger

Toolbar **Check score** → after a finished job: **Re-check score**.  
Optional JD on the score request (≤4000, sanitized). Dirty → save first.

## Job lifecycle

`queued` → `processing` → `complete` | `failed`  
UI stepper + poll with client timeout.

## Result rail

- Overall /100  
- Categories (name, score, evidence; deductions/suggestions in full payload)  
- Optional engine, GitHub enrichment, duration  
- `jd_match` when JD provided (matched/missing keywords, relevance)

## Engines

| Backend | Role |
|---------|------|
| `hiring_agent` | Real scoring path |
| `stub` | Deterministic demo |

## GitHub: cache only

Score uses **Settings → Update GitHub data** snapshot. **No** live GitHub call per score.

| Cache | Effect |
|-------|--------|
| Present | OSS/repo signal can enrich |
| Missing | Score still runs; weak GitHub signal; Settings warns |

## Outcomes matrix

| Situation | User sees |
|-----------|-----------|
| Running | Stepper advances; Scoring… status |
| Complete | Overall + categories; toast with score |
| Failed | Rail error + toast |
| Timeout | “Score timed out — try again” |

## Hard rules

1. Async job + stepper required.  
2. Overall + categories + evidence minimum.  
3. GitHub from user cache only.  
4. Never auto-score after AI edits.  
5. Manual re-score only.

## Done check

- [x] Stepper states  
- [x] Re-check label after first job  
- [x] No auto-score after generate

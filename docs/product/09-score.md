# Score (ATS-style async evaluation)

## Purpose

Produce an overall score and category breakdown (with evidence, deductions, suggestions) so the user can prioritize improvements and ground the coach. Scoring is always a **manual** user action.

## Trigger

Toolbar **Score** group:

- First time: **Check score**  
- After a job has completed or failed once: **Re-check score**

Optional JD text from the coach panel is sent with the job (max 4000 chars, sanitized).

Dirty resumes are saved before scoring starts.

## Async job lifecycle

1. Server creates a job in **queued**.  
2. Client polls until **complete** or **failed** (UI polls repeatedly with a timeout budget).  
3. Intermediate **processing** updates the stepper.  
4. Progress stepper labels: **Queued → Processing → Complete**; **Failed** is a distinct rose state.

### Timeout

If the job does not finish within the client wait window:

- Status: **Score timed out — try again**  
- Matching toast  
- User can re-check later (job may still finish server-side; rebuilders should still handle poll timeout gracefully).

## Result display (left rail)

When complete:

- Large **overall score** out of 100.  
- Optional meta: engine name, GitHub enrichment flag, duration.  
- **Categories** list: humanized name, score, evidence snippet.  
- Category model includes room for deductions and suggestions (coach consumes full score JSON even if the rail shows a compact view).

When failed: error message in the rail + toast.

## Score engines (configuration)

| Backend | Role |
|---------|------|
| **hiring_agent** | Real scoring path using vendored HackerRank hiring-agent style evaluation (default for serious local use) |
| **stub** | Deterministic demo scores without full LLM/agent stack |

Health endpoint reports `score_backend`.

## Categories (product contract)

Typical categories include (names may appear with underscores in data, spaces in UI):

- technical skills  
- open source  
- self projects  
- production  
- (and JD relevance via `jd_match` when a job description was provided)

Each category carries:

- score 0–100  
- evidence string  
- deductions list  
- suggestions (section, suggestion text, priority; optional expected impact)

### JD match surface

When a JD was provided, result includes match metadata such as:

- whether JD was provided  
- matched / missing keywords  
- relevance score  

Stub engine can still compute lightweight keyword match against resume text.

## GitHub signal — cache only

**Hard product rule:** scoring uses the user’s **cached GitHub snapshot** from Settings (**Update GitHub data**). It does **not** call GitHub live on every score click.

| Situation | Product expectation |
|-----------|---------------------|
| Cache present | Open-source / repo signal can enrich the score; UI may show GitHub enrichment |
| Cache missing | Score still runs; GitHub-related signal weak/absent; Settings warns “No cache yet” |
| Username on resume only | Profile cache is still the scoring source of truth for GitHub data |

See [Settings & GitHub](./10-settings-github-theme.md).

## Manual re-score only

After coach apply, generate, or manual edits:

- Score numbers **do not** auto-refresh.  
- User must press **Re-check score**.  
This matches the PRD scoring contract that remains valid in the current product.

## Rebuild rules

1. Async job + stepper UX required (not a single blocking spinner with no states).  
2. Overall + categories + evidence minimum.  
3. JD optional; sanitize; surface match when provided.  
4. GitHub from **user cache only** during score.  
5. Never auto-score after AI edits.

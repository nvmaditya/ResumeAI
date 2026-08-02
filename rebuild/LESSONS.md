# LESSONS.md — ResumeAI workspace memory

Product-intent and process mistakes for agents working in this workspace.  
**Read before a phase. Append after any wrong-foot or repeated correction.**

Cross-project durable prefs (tooling habits, not product roadmap): `~/.grok/memory/MEMORY.md`.  
Progress by phase: [`PLAN.md`](./PLAN.md) progress log.  
Binding process: [`AGENTS.md`](./AGENTS.md) § Development process (binding).

---

## How to append

Use this template (one entry per lesson):

```markdown
### YYYY-MM-DD — short title
- **Wrong:** what was assumed or shipped incorrectly
- **Correct:** the binding rule
- **Doc:** link to PRD / docs/product / AGENTS section
```

---

## Lessons

### 2026-08-01 — Form path is not AI Generate + track flip
- **Wrong:** Shipping “New AI resume” + AI Generate that flips track to LATEX_ONLY and removes the form after generate (old Phase 5 / monorepo Journey A).
- **Correct (grilling lock):** **New resume** form-only; **Compile** = deterministic form→LaTeX+PDF; stay `structured`; no Source tab; Lint hidden; `.tex` = last compile snapshot; PDF goes stale until recompile. **New LaTeX** keeps source editor + rule-based lint with fix hints. No fake AI branding/toasts.
- **Doc:** grilling shared understanding; `tests/test_form_path_pivot.py`

### 2026-08-01 — Process is skills-guide + product map, not vision PRD
- **Wrong:** Treating monorepo root vision PRD (template picker, free-form chat) as MVP.
- **Correct:** Product target is this workspace `PRD.md` + `docs/product/`; process loop and skill when-to-use come from `C:\Code\skills-guide`; phase skill table stays in `PLAN.md`.
- **Doc:** [`AGENTS.md`](./AGENTS.md) § Mission, § Development process; [`docs/product/11-constraints-and-out-of-scope.md`](./docs/product/11-constraints-and-out-of-scope.md)

### 2026-08-01 — No early stop on verification
- **Wrong:** Claiming a slice done after a single green unit test.
- **Correct:** Multi-pass: hard-rule test + binding product doc match + verification-before-completion/check-work + traps still true. Budget buys depth, not skipping the loop.
- **Doc:** [`AGENTS.md`](./AGENTS.md) § Multi-pass verification; skills-guide `HOW_TO_WORK.md` § Quality without thrash

### 2026-08-01 — UI taste after structure
- **Wrong:** Applying high-end-visual-design / taste skills before chrome and product structure work.
- **Correct:** Spec owns structure; taste polish after chrome works; product docs win on conflicts with pure aesthetics.
- **Doc:** [`AGENTS.md`](./AGENTS.md) § Development process; skills-guide UI rule

### 2026-08-01 — Product naming is ResumeAI only
- **Wrong:** Branding service/UI/docs with a secondary workspace label.
- **Correct:** Name is **ResumeAI** / `resumeai`. Process comes from skills-guide; product contract from PRD + docs/product.
- **Doc:** [`README.md`](./README.md), health `service` field

### 2026-08-01 — Clear React session on 401, not only localStorage
- **Wrong:** On list 401, call `clearToken()` + navigate to login while React `token` state stays set → “authed on auth pages” effect bounces back to home.
- **Correct:** `setTokenState(null)` (shared `endSessionToLogin` / `routeAfterUnauthorized`) so `hasSession` is false and login sticks.
- **Doc:** [`docs/product/01-auth-and-session.md`](./docs/product/01-auth-and-session.md); `frontend/src/authGuard.ts`

<!-- Append new lessons above this line (or below in reverse chrono). -->

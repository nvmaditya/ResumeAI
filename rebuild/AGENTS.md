# AGENTS.md — ResumeAI product workspace

Rules for coding agents working **in this workspace** (or implementing a new app according to this workspace’s PRD/docs).  
This file does **not** replace monorepo root `AGENTS.md` for the **live** app; use root AGENTS when editing monorepo `backend/` / `frontend/` in place.

**Process (binding):** always work per **`C:\Code\skills-guide`** — [`HOW_TO_WORK.md`](file:///C:/Code/skills-guide/HOW_TO_WORK.md) + [`SKILLS_GUIDE.md`](file:///C:/Code/skills-guide/SKILLS_GUIDE.md). Product *what* is PRD + `docs/product/`; skills-guide is *how*. Phase skill map: [`PLAN.md`](./PLAN.md).

---

## Mission

Implement ResumeAI to **current shipped product parity** as defined by:

1. [`PRD.md`](./PRD.md)  
2. [`docs/product/`](./docs/product/README.md) (product-v2 content)  
3. [`PLAN.md`](./PLAN.md) phases  

Do **not** implement root monorepo `PRD.md` vision items as MVP unless the product PRD lists them as shipped.

---

## Development process (binding)

This section is **mandatory**, not optional advice. Process source of truth for *how* to work:

| Source | Role |
|--------|------|
| `C:\Code\skills-guide` → [`HOW_TO_WORK.md`](file:///C:/Code/skills-guide/HOW_TO_WORK.md) + [`SKILLS_GUIDE.md`](file:///C:/Code/skills-guide/SKILLS_GUIDE.md) | General process loop and when-to-use skills (any project) |
| This file + [`PLAN.md`](./PLAN.md) § Skills | Product phase → skill map and hard gates |
| [`PRD.md`](./PRD.md) + [`docs/product/`](./docs/product/) | *What* to build; wins over monorepo vision PRD |

Do **not** fork skills-guide into this tree or turn skills-guide into a ResumeAI roadmap. Link out; keep phase tables here.

### Default loop (must follow)

```
Think → Plan → Implement (small) → Verify → Review → Next
```

| Stage | Required skills / rules |
|-------|-------------------------|
| **Think** | `brainstorming` / `grilling` only when product docs do not settle the decision |
| **Plan** | `writing-plans` (or bundled `design` for large architecture); phase order from `PLAN.md` |
| **Implement** | **`test-driven-development`** for hard product rules + always-on **ponytail** |
| **Domain** | `resume-latex`, `resume-latex-generate`, `resume-template` before touching compile/generate/templates |
| **Debug** | `systematic-debugging` / `diagnosing-bugs` — do not thrash |
| **Done** | **`verification-before-completion`** + **`check-work`** (multi-pass; see below) |
| **Review** | `review` / `requesting-code-review`; optional `ponytail-review` |
| **Parallel** | **`dispatching-parallel-agents`** only for **independent** tracks (never tightly coupled state machines, same migration, or shared dirty modules) |
| **Seams** | **`codebase-design`** when introducing or hardening replaceable module boundaries |
| **UI polish** | Structure and product chrome first from `docs/product/`; then **`high-end-visual-design`** / `design-taste-frontend` / `minimalist-ui` — **never** polish before chrome works |

**Hard-rule pattern (every trap / trust boundary / contract field):**

1. Read the binding product doc for the slice.  
2. Write a **failing** automated check first (**test-driven-development**).  
3. Minimum implement (**ponytail**).  
4. Multi-pass verify (below). **Never** claim done on a single green unit test alone.

**Always-on:** **ponytail** (YAGNI, reuse, stdlib first, fewest files). User may set lite/full/ultra/off; default is full.

### Multi-pass verification — no early stopping

Before any slice or phase is claimed **done**, agents **must** complete **all** of the following. Token/time budget buys **depth** (more tests, E2E, design polish)—**not** skipping this loop (skills-guide § Quality without thrash).

| Pass | What | Fail ⇒ |
|------|------|--------|
| 1 | **Hard-rule automated check** for the slice’s critical product rule | Not done |
| 2 | Behavior matches binding **`docs/product/…`** + **PRD** acceptance for that slice | Not done |
| 3 | **`verification-before-completion`** and/or **`check-work`**-style re-check of the slice (diffs, tests, traps still true) | Not done |
| 4 | No out-of-scope vision creep (template picker, free-form chat, permanent Form after generate, auto-score, etc.) | Not done |
| 5 | Memory updates if intent was wrong-footed: append [`LESSONS.md`](./LESSONS.md); brief [`PLAN.md`](./PLAN.md) progress log | Incomplete hygiene |

**Forbidden cost-cutting / early stopping:**

- Stopping after one green unit test without re-checking the binding product doc and traps.  
- Skipping `check-work` / `verification-before-completion` because “it looks fine.”  
- Claiming phase exit without the phase’s hard-rule test.  
- Parallelizing coupled work to “go faster” in ways that hide integration bugs.

Process scaffolding itself is guarded by `tests/test_process_contract.py` (must stay green).

### Memory system (project + durable prefs)

| Artifact | Purpose | When |
|----------|---------|------|
| [`LESSONS.md`](./LESSONS.md) | Product-intent mistakes and correct rules (workspace memory) | **Read** before a phase; **append** after any wrong-foot or repeated correction |
| [`PLAN.md`](./PLAN.md) progress log | What phase advanced and brief note | Append after meaningful slice progress |
| `~/.grok/memory/MEMORY.md` | Cross-project durable prefs (agent/tooling habits) | Read/update for **global** prefs only—not product roadmap |

Later sessions must not re-learn the same failures: re-read `LESSONS.md` + relevant product doc before implementing.

### Modular growth contract (seams)

Replaceable seams must stay **swappable boundaries**. Depend **inward** on interfaces; swap implementations at the boundary. Do **not** hard-wire cross-cutting logic into UI-only layers or single mega-modules. When introducing or hardening seams, use **`codebase-design`**.

| Seam | Role | Swap later for |
|------|------|----------------|
| **auth** | Register/login/session/JWT | Different IdP / session store |
| **compile** | LaTeX → PDF (tectonic primary, layout fallback) | Other TeX engines |
| **score** | ATS scoring job | hiring-agent vs stub vs remote |
| **jobs** | Async score (and similar) progress | Queue/worker backends |

New work must not collapse these into one file or call remote GitHub from score without the Settings cache boundary.

---

## Product constraints (non-negotiable)

### Trust & AI

- Sanitize JD and edit payloads; treat resume/JD as untrusted data for models.  
- **No auto-score** after generate.  
- Generate: always surface **`used_llm`** (AI vs **template fallback**).  
- When a live generate backend is configured, generate must use it on the real request path—not stub-only in production wiring.

### Create & modes

- Create CTAs: **New AI resume** + **New LaTeX** only.  
- **No** user-facing template picker as primary create.  
- After New AI **AI Generate** success: track → **`latex`**, workspace **source-only** (Form + AI Generate **gone**).  
- Contact links on **resume form**, not Settings-only.

### Score & GitHub

- Score is async with progress stepper.  
- GitHub data for scoring comes from **Settings → Update GitHub data** cache only—not live GitHub on every score.

### Compile & files

- Prefer **tectonic**; layout PDF fallback allowed; **never** corrupt/fake PDFs.  
- Preview: browser **iframe** + blob—not pdf.js/SyncTeX as requirements.  
- Downloads: PDF and `.tex` when source exists.

### Chrome

- Two-tier header: identity + **File | Build | Score | Danger**.  
- Rail · editor · PDF.  
- Light/dark theme with reduced-motion respect.

### Engineering discipline

- **Ponytail:** minimum code; no new deps if stdlib/existing stack covers it; boring over clever.  
- Modular seams (auth, compile, score, jobs) for later replacement — see **Modular growth contract** above.  
- Local-first; absolute filesystem paths must not leak into user-facing DB as required UX.  
- Never commit secrets, `.env`, personal resume samples, or venv/node_modules dumps as product source.

---

## How to use docs in this workspace

| Question | Read |
|----------|------|
| What is in / out of scope? | `PRD.md` §8–9, `docs/product/11-…` |
| Exact UX for a control? | Matching `docs/product/0x-…` |
| Build order? | `PLAN.md` |
| Product traps? | `docs/product/README.md` top traps |
| How to work (process)? | **Development process (binding)** above + `C:\Code\skills-guide` |
| Which skills when (general)? | `C:\Code\skills-guide` (`HOW_TO_WORK.md`, `SKILLS_GUIDE.md`) |
| Skills for this product’s phases? | `PLAN.md` § Skills |
| Past product-intent mistakes? | [`LESSONS.md`](./LESSONS.md) |
| Cross-project agent prefs? | `~/.grok/memory/MEMORY.md` |

When skills are installed or removed, update the **general** repo `C:\Code\skills-guide` (see `MAINTENANCE.md` and always-on `skills-guide-sync` rule). Keep product-only phase maps in this workspace.

When product docs and old monorepo vision PRD conflict → **this workspace PRD + docs/product win**.  
When high-end visual taste conflicts with specified chrome/traps → **product docs win for structure**; taste skills polish **within** that shell.

---

## Done expectations (for an implementation slice)

Before claiming a phase or feature is complete, complete the **multi-pass verification** table above. In short:

1. Behavior matches the relevant **docs/product** section and **PRD** acceptance items for that slice.  
2. No silent introduction of out-of-scope vision (template picker, permanent Form after generate).  
3. Include at least one **automated check** that fails if the critical product rule for that slice regresses (e.g. track flip after generate, used_llm field, create CTAs only).  
4. Second pass: **`verification-before-completion`** / **`check-work`** against binding doc + traps—not a single green test alone.  
5. Update this workspace `README.md` / phase notes in `PLAN.md` if the product’s public surface changes.  
6. If you wrong-foot product intent, append a concrete lesson to [`LESSONS.md`](./LESSONS.md).

### Local verification commands (this workspace)

```bash
# Prefer uv (skills-guide implement loop; no early stop — run suite twice when claiming done)
cd backend && uv sync --group dev && cd ..
uv run --project backend pytest tests/ -q
```

When app code exists: unit/API tests for the slice; Journey A/B as applicable; traps still hold.

When implementing **against the live monorepo** instead of a greenfield tree, also obey root `AGENTS.md` done gate (`scripts/verify_before_done.py`).

---

## Explicit do-nots

- Do not reintroduce primary “From template” create.  
- Do not claim permanent Form|Source after New AI generate.  
- Do not auto-trigger score after generate.  
- Do not call GitHub on every score (cache only).  
- Do not leave generate fallback looking like a live model without `used_llm` honesty.  
- Do not delete monorepo `docs/product-v2/` or live app as part of scaffolding.  
- Do not skip multi-pass verification or claim done after one unit test only.  
- Do not polish with high-end taste skills before product chrome/structure works.  
- Do not use `dispatching-parallel-agents` on tightly coupled state or shared migrations.

---

## Stack reminder (high level)

FastAPI + React/Vite/TS/Tailwind + SQLite + JWT + tectonic/layout + hiring-agent/stub + generate backends (ollama/openrouter/groq/stub). Details: PRD §7 and product docs hub.

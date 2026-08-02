# Implementation plan — ResumeAI current product

Phased plan to implement the product described in [`PRD.md`](./PRD.md) and [`docs/product/`](./docs/product/README.md).  
Each phase is shippable in isolation; later phases depend on earlier ones. Do not reorder past phases without updating this doc.

---

## Principles

1. **Product docs first** — behavior comes from `docs/product/`, not from inventing UX.  
2. **Traps first** — never “temporarily” ship template picker or dishonest generate fallback.  
3. **Vertical slices** — each phase ends with a user-visible capability + automated regression for its hard rule.  
4. **Modes explicit** — model FORM_PATH vs LATEX_ONLY early (track field), even before full generate quality.

---

## Skills (how to build each phase)

**General** skill usage (any project): `C:\Code\skills-guide`  
→ `HOW_TO_WORK.md` (process) · `SKILLS_GUIDE.md` (when-to-use) · `INVENTORY.md`

**Binding process contract:** [`AGENTS.md`](./AGENTS.md) § **Development process (binding)** — skills-guide loop, TDD, multi-pass verification (**no early stop**), memory, modular seams.

**Default loop:** Think → Plan → Implement (small) → Verify → Review.

| Stage | Skills |
|-------|--------|
| Think | `brainstorming` / `grilling` only if docs don’t settle it |
| Plan | `writing-plans` (or `design` for big seams) |
| Implement | **`test-driven-development`** + always-on **ponytail** |
| Domain (this product) | `resume-latex`, `resume-latex-generate`, `resume-template` as relevant |
| Debug | `systematic-debugging` / `diagnosing-bugs` |
| Done | **`verification-before-completion`** / **`check-work`** (multi-pass; not one unit test alone) |
| Review | `review` + optional `ponytail-review` |
| Parallel | **`dispatching-parallel-agents`** only for **independent** tracks (never coupled state) |
| Seams | **`codebase-design`** when introducing/hardening replaceable boundaries |
| UI polish | Structure first; then **`high-end-visual-design`** / `design-taste-frontend` / `minimalist-ui` (esp. Phase 9) |

**Quality bar:** hard-rule test every phase (bug-free); structure first, visual polish Phase 9 (beautiful).  
**No early stopping:** budget buys depth, not skipping verify/review. See AGENTS multi-pass table.  
**Memory:** append [`LESSONS.md`](./LESSONS.md) on product-intent mistakes; update progress log below; global prefs in `~/.grok/memory/MEMORY.md`.  
**Skill installs/removes:** update general `C:\Code\skills-guide` (not this PLAN) via always-on `skills-guide-sync`.

### This product — phase skill cheat-sheet

| Phase | Primary skills | Hard rule |
|-------|----------------|-----------|
| 0 Scaffold | writing-plans, ponytail, verification-before-completion, check-work | Process + product contract files present (`tests/test_process_contract.py`) |
| 1 Auth | test-driven-development, ponytail, check-work | Unauth blocked |
| 2 Create | test-driven-development, ponytail, verification-before-completion | No template picker CTA |
| 3 Workspace | test-driven-development; structure before taste; optional high-end-visual-design after shell works | LATEX_ONLY: no Form / AI Generate |
| 4 Compile | **resume-latex**, systematic-debugging, test-driven-development | Valid PDF, never corrupt |
| 5 Generate | **resume-latex-generate**, test-driven-development, check-work | `used_llm` + track flip |
| 6 Versions | test-driven-development, ponytail | Restore works |
| 7 Score | test-driven-development, **codebase-design**, diagnosing-bugs | GH cache only; no auto-score |
| 9 Polish | **high-end-visual-design**, design-taste-frontend / minimalist-ui, playwright-skill | Full acceptance script; traps still true |
| 10 Hardening | **codebase-design**, ponytail-review, verification-before-completion, check-work | Health + modular seams (auth, compile, score, jobs) |

**Parallel work:** use `dispatching-parallel-agents` when two phases or tracks are independent (e.g. docs/process vs unrelated stub); never for shared track/mode state or one migration.

---

## Phase 0 — Workspace & contract lock

**Goal:** Scaffold app shells; wire this PRD/docs as the contract; bind skills-guide process + memory.

- [x] Create backend/frontend project structure (or clear package layout).  
- [x] Health endpoint (or equivalent) stub.  
- [x] README for how to run the new app.  
- [x] Automated test: this workspace still contains PRD + product docs + AGENTS + this plan + LESSONS + process/memory headings (`tests/test_process_contract.py`).  
- [x] Binding process in AGENTS: TDD, multi-verify no early-stop, parallel agents, high-end-visual-design timing, ponytail, domain skills, modular seams, memory.
- [x] Health hard-rule test drives shipped `create_app` (`tests/test_health.py`); modular seam packages under `backend/app/`.

**Exit:** Empty app boots; agents know constraints. Process contract green even before app code.

**Docs:** `PRD.md`, `docs/product/README.md` traps, `AGENTS.md` process section, `LESSONS.md`.

---

## Phase 1 — Auth & session

**Goal:** Register, login, logout, protected routes.

- [x] Email + password (≥ 8); register → auto-login.  
- [x] JWT (or equivalent) session storage.  
- [x] Redirect unauthenticated users to login.  
- [x] Logout clears session.

**Exit:** Journey step “register → home” works.

**Docs:** `docs/product/01-auth-and-session.md`  
**Hard rule test:** unauthenticated access to protected resume list fails/redirects (`tests/test_auth.py`).

---

## Phase 2 — Resume list & create paths

**Goal:** Multi-resume CRUD skeleton + two create CTAs only.

- [x] List resumes (empty state with both CTAs).  
- [x] **New AI resume** → track `structured`, empty form JSON.  
- [x] **New LaTeX** → track `latex`, starter document.  
- [x] Delete with confirm.  
- [x] Search + tag filter (can be thin initially).

**Exit:** Open created resume by id.

**Docs:** `docs/product/02-resumes-list-and-create.md`  
**Hard rule test:** no “From template” / template picker primary CTA in UI (`tests/test_resumes.py`).

---

## Phase 3 — Workspace chrome & editor shell

**Goal:** Two-tier chrome; rail · editor · PDF panes; dirty/save; title/tags.

- [x] Identity row + File|Build|Score|Danger toolbar (buttons may stub).  
- [x] FORM_PATH: Form|Source tabs; LATEX_ONLY: source only.  
- [x] Structured form fields (basics + main lists).  
- [x] LaTeX source editor (syntax optional later; editing required).  
- [x] Save title/tags/body.

**Exit:** Edit and save both tracks.

**Docs:** `docs/product/03-workspace.md`, `04-form-source-editor.md`  
**Hard rule test:** LATEX_ONLY resume has no Form tab / no AI Generate (`tests/test_workspace.py`, `workspaceMode.ts`).

---

## Phase 4 — Compile, PDF preview, lint, downloads

**Goal:** LaTeX → PDF path and preview.

- [x] Compile (tectonic if available, else layout fallback).  
- [x] Iframe PDF preview; no corrupt stubs.  
- [x] Debounced auto-preview optional but recommended.  
- [x] Lint → diagnostics list with line jump.  
- [x] Download PDF and `.tex`.

**Exit:** Compile shows PDF; downloads work.

**Docs:** `docs/product/08-compile-pdf-lint-downloads.md`  
**Hard rule test:** compile produces valid PDF bytes (header `%PDF`) — `tests/test_compile.py`.

---

## Phase 5 — AI Generate + track flip

**Goal:** Form → LaTeX with honesty and mode transition.

- [x] AI Generate on FORM_PATH only.  
- [x] Seed + repair loop (LLM or deterministic fallback).  
- [x] Return and display **`used_llm`** (AI vs template fallback).  
- [x] On success: track → `latex`; UI **source-only**; AI Generate removed.  
- [x] Quiet recompile after success.

**Exit:** Journey A through generate complete.

**Docs:** `docs/product/05-ai-generate.md`, modes in hub  
**Hard rule test:** after generate, track is latex and form chrome gone; used_llm surfaced — `tests/test_generate.py`.

---

## Phase 6 — Versions

**Goal:** LaTeX checkpoints.

- [x] Commit with message; unchanged detection.  
- [x] List, restore (→ source, recompile), delete with confirm.

**Exit:** Restore older LaTeX.

**Docs:** `docs/product/07-versions.md`  
**Hard rule test:** commit → unchanged no-op → restore content → delete; unauth denied — `tests/test_versions.py`.

---

## Phase 7 — Score + GitHub cache

**Goal:** Async scoring + Settings GitHub cache.

- [x] Settings: username, Save, **Update GitHub data**, cache status.  
- [x] Score job: queued → processing → complete|failed stepper.  
- [x] Overall + categories; optional JD.  
- [x] Score reads **cache only** (no live GitHub per score).  
- [x] Manual Check / Re-check only.

**Exit:** Score completes with and without cache.

**Docs:** `docs/product/09-score.md`, `10-settings-github-theme.md`  
**Hard rule test:** score path uses cached snapshot; no auto-score after edit helpers — `tests/test_score.py`.

---

## Phase 9 — Theme, polish, multi-resume UX

**Goal:** Light/dark wipe; list polish; empty/error/timeout parity with product docs outcomes matrices.

- [x] Theme toggle + reduced motion.  
- [x] Toasts/status for key operations.  
- [x] Score timeout messaging; version unchanged toast; etc.  
- [x] Hard-rule tests `tests/test_phase9_polish.py` + `theme.test.ts`; traps still true.

**Exit:** Acceptance script passes; traps list still true.

**Docs:** `docs/product/10-…`, `11-…`, PRD §10  
**Hard rule test:** theme default light + reduced-motion + score timeout copy + version unchanged — `tests/test_phase9_polish.py`.

---

## Phase 10 — Hardening & seams

**Goal:** Production-minded local MVP.

- [ ] Env config for score/generate/tectonic backends.  
- [ ] Health reports live backends.  
- [ ] Modular ScoreEngine / Compiler boundaries (auth, compile, score, jobs — depend inward, swap at boundary; **codebase-design**).  
- [ ] LESSONS.md updates for any product-intent mistakes (ongoing memory hygiene).

**Exit:** Documented runbook; env table; health green; seams still replaceable.

---

## Dependency graph (summary)

```
0 → 1 → 2 → 3 → 4 → 5 → 6
              ↘       ↗
                7 → 9 → 10
```

Phase 7 (score) can start after Phase 3 if score only needs content strings; ideally after 4–5 for real resume text.

---

## Out of order / forbidden shortcuts

| Shortcut | Why forbidden |
|----------|----------------|
| Template picker “until generate works” | Wrong create product |
| Skip used_llm | Dishonest AI UX |
| Skip track flip | Invisible or dual-mode wrong chrome |
| Auto-score after generate | Violates scoring contract |

---

## Progress log (agents: append briefly)

| Date | Phase | Note |
|------|-------|------|
| — | 0 | Workspace scaffolded with PRD, AGENTS, PLAN, product-v2 docs copy |
| 2026-08-01 | — | Linked general skills-guide; product phase skill cheat-sheet kept in this PLAN only |
| 2026-08-01 | 0 | Binding process contract: multi-verify/no early-stop, LESSONS.md, modular seams table, `tests/test_process_contract.py` |
| 2026-08-01 | 0 | Coding started: FastAPI health + seam packages, Vite shell, `tests/test_health.py` / `test_seams.py` |
| 2026-08-01 | 1 | Auth: register auto-login, bearer sessions, protected `/resumes`, logout; FE login/register/home; `tests/test_auth.py` |
| 2026-08-01 | 2 | Resume list/create AI+LaTeX, get/delete, search+tag AND filter; FE two CTAs only; `tests/test_resumes.py` |
| 2026-08-01 | 3 | Workspace chrome File|Build|Score|Danger; FORM_PATH vs LATEX_ONLY; form+source save; `tests/test_workspace.py` |
| 2026-08-01 | 4 | Compile tectonic/layout `%PDF`; lint; PDF/.tex download; iframe+blob preview; `tests/test_compile.py` |
| 2026-08-01 | 5 | AI Generate form→LaTeX, used_llm honesty, track flip LATEX_ONLY; `tests/test_generate.py` |
| 2026-08-01 | 6 | LaTeX checkpoints: commit/list/restore/delete + unchanged no-op; rail wired; `tests/test_versions.py` |
| 2026-08-01 | pivot | Form-path grill: New resume; Compile form→PDF no flip; no AI Generate/Source/Lint on form; latex lint suggestions; `tests/test_form_path_pivot.py` |
| 2026-08-01 | 7 | Async score job + Settings GitHub cache (stub engine, cache-only, manual Check/Re-check); `tests/test_score.py` |
| 2026-08-02 | 9 | Theme light/dark + reduced-motion wipe; toasts; score timeout + version unchanged; list empty/filter polish; `tests/test_phase9_polish.py` + `theme.test.ts` |


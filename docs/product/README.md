# ResumeAI — Product documentation (current shipped state)

This folder is the **rebuild-from-scratch product bible** for ResumeAI as it exists today.  
It describes **what the product does for users**, **how each capability behaves**, and **hard product rules** that keep a rebuild correct—not how the code is organized.

| Doc | Covers |
|-----|--------|
| [01 — Auth & session](./01-auth-and-session.md) | Register, login, JWT session, logout, protected routes |
| [02 — Resume list & create](./02-resumes-list-and-create.md) | Multi-resume CRUD, New AI resume, New LaTeX, search/tags |
| [03 — Workspace chrome](./03-workspace.md) | Two-tier header, toolbar groups, rail · editor · PDF layout |
| [04 — Form, source & editor](./04-form-source-editor.md) | Structured form fields, Form \| Source tabs, CodeMirror, dirty state |
| [05 — AI Generate](./05-ai-generate.md) | Form → LaTeX, quality loop, `used_llm` honesty, toasts |
| [06 — Coach](./06-coach.md) | Fixed actions, JD, hunks, apply selected/all, no free-form chat |
| [07 — Versions](./07-versions.md) | Commit, restore, delete checkpoints |
| [08 — Compile, PDF, lint, downloads](./08-compile-pdf-lint-downloads.md) | Tectonic/layout, preview, lint diagnostics, .pdf / .tex |
| [09 — Score](./09-score.md) | Async jobs, hiring-agent vs stub, JD match, GitHub cache only |
| [10 — Settings, GitHub, theme, shell](./10-settings-github-theme.md) | Profile, Update GitHub data, light/dark wipe, app chrome |
| [11 — Constraints & out of scope](./11-constraints-and-out-of-scope.md) | Trust boundaries, rebuild rules, PRD items **not** shipped |

**Companion sources (not substitutes for this folder):** root [`README.md`](../../README.md) (quick start + feature summary), [`LESSONS.md`](../../LESSONS.md) (hard-won product rules), [`PRD.md`](../../PRD.md) (**vision only**—do not treat as current product).

---

## What ResumeAI is

ResumeAI is a **local-first** web app for software engineers who want to:

1. Own one or many resumes (structured form → AI LaTeX, or paste raw LaTeX).
2. **Compile** them to PDF with Overleaf-like fidelity when tectonic is available.
3. **Score** them with an ATS-style engine (vendored HackerRank hiring-agent, or a stub for offline demos), optionally grounded on a job description and **cached** GitHub profile data.
4. **Coach** improvements via a small set of **fixed actions** that propose find/replace hunks the user can select and apply—**never** free-form chatbot messages from the client.

It is shaped like a future SaaS (auth, multi-resume, jobs, object storage seams) but runs fully on one machine for the MVP.

**Primary audience:** technical candidates who care about impact wording, project strength, JD alignment, and GitHub signal.

---

## Technology (high level only)

Use this only as context for a from-scratch rebuild—not as an implementation guide.

| Layer | Choice (current) |
|-------|------------------|
| Backend API | FastAPI (Python 3.12+), REST under `/api/v1` |
| Frontend | React + Vite + TypeScript + Tailwind |
| Database | SQLite (local) |
| Auth | Email + password, JWT bearer token in browser storage |
| File/object storage | Local filesystem store (S3-shaped seam later) |
| Background jobs | In-process job runner (score jobs) |
| LaTeX → PDF | **Tectonic** preferred; simple **layout PDF** fallback if binary missing |
| Scoring | `hiring_agent` (default) or `stub` |
| Coach / generate LLMs | `ollama` · `openrouter` · `groq` · `stub` |
| PDF preview | Browser-native iframe + blob URL (no pdf.js, no SyncTeX) |
| LaTeX editor | CodeMirror-based source editor with theme-aware highlighting |

Env-facing health endpoint reports live backends: score engine, latex engine, coach backend/model.

---

## Happy-path user journeys

### A — AI resume (primary create path)

1. **Register** (email + password ≥ 8) → auto-login → **Resumes** list.
2. Optional: **Settings** → set **GitHub username** → **Update GitHub data** (cache for scoring).
3. **New AI resume** → empty structured form opens (track: structured).
4. Fill **basics**, work, education, skills, projects, etc. → **Save** as needed.
5. **AI Generate** → LaTeX produced; toast says **AI** or **template fallback** (`used_llm`); track becomes **latex**; UI is **source-only** (Form tab and AI Generate go away).
6. **Compile** (or auto-preview after debounce) → PDF pane updates; engine chip may show `tectonic` or layout.
7. Optional: paste **job description** in coach panel → **Check score** → progress **queued → processing → complete** → overall + categories.
8. Coach: pick a **fixed action** → review reply + hunks → checkboxes → **Apply selected** (or all) → source updates → recompile.
9. **Commit** a version in the left rail; **PDF** / **.tex** download when ready.
10. Score is **never** auto-rerun after coach apply—user must **Re-check score**.

### B — Own LaTeX

1. **New LaTeX** → starter document opens (track: latex).
2. Edit source (undo/redo), **Compile**, **Lint**, **Score**, **Coach**, versions, downloads—same workspace chrome.
3. No Form tab (source-only path).

### C — Multi-resume day-to-day

1. From **Resumes**: search by title/track/tag; filter by tag chips; open or **Delete** with confirm.
2. Edit title and tags on the workspace identity row; dirty indicator until **Save**.

---

## Product surface map (inventory)

| Area | User-facing? | Notes |
|------|--------------|--------|
| Register / Login / Logout | Yes | Session token; unauthenticated users redirected to login |
| Resume list + create + delete | Yes | AI-first + LaTeX only |
| Structured form + AI Generate | Yes | Form \| Source **pre-generate** (track structured); after generate track→**latex**, **source-only** (Form + AI Generate gone) |
| LaTeX source editor | Yes | Coach highlights, undo/redo |
| Floating coach | Yes | Fixed actions only |
| Versions commit/restore/delete | Yes | Left rail |
| Compile + PDF preview | Yes | Auto-debounce + manual Compile |
| Lint + diagnostics list | Yes | Jump to line in source |
| Score job + stepper + categories | Yes | Manual trigger only |
| Settings drawer + GitHub cache | Yes | Contact links live on resume form, not settings |
| Light / dark theme | Yes | Diagonal wipe; reduced-motion honored |
| Health / env backends | Ops-facing | `GET /api/v1/health` |
| Template catalog API | Internal / legacy | **No primary user template picker** |
| PDF/DOCX extract | API stub only | **Not** a primary create path in UI |
| Free-form coach chat | **No** | Trust boundary |
| GitHub OAuth live-per-score | **No** | Cache-only for scoring |
| Monetization / tiers | **No** | Out of scope |

---

## How to use these docs when rebuilding

1. Rebuild **journeys A and B** end-to-end before polish.
2. Treat **[11 — Constraints](./11-constraints-and-out-of-scope.md)** as acceptance tests for product correctness (especially coach, generate honesty, GitHub cache, no template picker, no auto-score after apply).
3. Match empty/error/timeout UX called out in feature docs (toasts, confirm dialogs, score timeout, compile failure after apply reverts source).
4. Use root `README.md` for run/env; use this folder for **what “done” means product-wise**.

---

## Document maintenance

When product behavior changes, update the relevant file here **and** the Features table in root `README.md`.  
If you ship a product-intent mistake, append a rule to `LESSONS.md`.

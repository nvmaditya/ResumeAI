# PRD: ResumeAI (current shipped product — product target)

**Status:** Binding product contract for this workspace  
**Version:** 2.0 (current-state contract)  
**Source of truth:** [`docs/product/`](./docs/product/README.md) (seeded from `docs/product-v2/`)  
**Not binding as current scope:** root monorepo `PRD.md` v1.1 vision (template picker, free-form chat, PDF/DOCX primary create)—those items are **future / out of scope** unless listed below as shipped.

---

## 1. Problem & product summary

Local-first web app for software engineers to:

1. Own **one or many** resumes via **New AI resume** (structured form → **AI Generate** → LaTeX) or **New LaTeX** (paste/edit source).  
2. **Compile** LaTeX to PDF (tectonic preferred; layout fallback).  
3. **Score** with an ATS-style engine (hiring-agent or stub), optional job description, **cached** GitHub profile data.

Audience: technical candidates who care about impact wording, projects, JD alignment, and GitHub signal.

Shape: future-SaaS seams (auth, multi-resume, jobs, object storage) on a single machine for MVP.

---

## 2. Success criteria (MVP = current product parity)

A user on one local machine can:

1. Register (email + password ≥ 8) and log in (JWT session).  
2. Create **New AI resume** and **New LaTeX** (no template picker).  
3. On AI path: fill form → **AI Generate** → see **AI** or **template fallback** toast (`used_llm`) → workspace becomes **source-only** (track `latex`; Form + AI Generate gone).  
4. Compile and see live PDF preview (browser iframe).  
5. Lint, download PDF and `.tex`.  
6. Manually **Check score** (async stepper); optional JD; GitHub from Settings cache only.  
7. Commit / restore / delete LaTeX versions.  
8. Settings: GitHub username + **Update GitHub data**; light/dark theme.  
9. Multi-resume list with search, tags, delete.

---

## 3. Workspace modes (required product model)

```
New AI resume → FORM_PATH (track=structured)
                  Form | Source · AI Generate
                  └─ AI Generate success
                       → LATEX_ONLY (track=latex)
                         Source only · no Form · no AI Generate

New LaTeX → LATEX_ONLY from the start
```

| Mode | Track | Editor | AI Generate |
|------|-------|--------|-------------|
| FORM_PATH | structured | Form \| Source | Yes |
| LATEX_ONLY | latex | Source only | No |

Legacy template-id resumes may keep form chrome—not the primary create flow.

---

## 4. User journeys

### A — AI resume (primary)

Register → optional Settings GitHub cache → New AI resume → fill form → AI Generate → LATEX_ONLY → Compile → Score → Versions → downloads → manual Re-check score.

### B — Own LaTeX

New LaTeX → edit source → Compile / Lint / Score / versions / downloads.

### C — Multi-resume

List search/tags; open; title/tags edit; delete with confirm.

---

## 5. Feature requirements (shipped)

### 5.1 Auth & session

- Email + password; register auto-logs in.  
- Bearer token in browser; unauthenticated → login.  
- Logout clears token.  
- No OAuth IdP required for MVP.

### 5.2 Resume list & create

- CTAs: **New AI resume**, **New LaTeX** only.  
- Search by title/track/tag; AND tag chips.  
- Delete with confirm.  
- **No** user-facing template picker; **no** PDF/DOCX extract as primary create.

### 5.3 Workspace chrome

- Two-tier: identity (title, track, engine, dirty, tags) + toolbar **File | Build | Score | Danger**.  
- Grid: rail (versions · diagnostics · score) · editor · PDF.  
- AI Generate visible **only** on FORM_PATH.

### 5.4 Form & source editor

- Structured form: basics, work, education, skills, projects, publications, awards, certifications.  
- Contact links on form (not Settings-only).  
- Source: LaTeX editor, undo/redo, diagnostic jump.  
- After New AI generate: **no** permanent dual Form|Source.

### 5.5 AI Generate

- Form → seed (LLM or deterministic fallback) → lint/compile repair loop.  
- Surface **`used_llm`** honestly (AI vs template fallback).  
- On success (primary path): persist track **latex**; drop Form + AI Generate.

### 5.6 Versions

- User commit of LaTeX with message; unchanged → no-op toast.  
- Restore / delete with confirm.  
- Not structured-form history.

### 5.7 Compile, PDF, lint, downloads

- Tectonic preferred; layout fallback; never corrupt fake PDFs.  
- Preview: browser iframe + blob (no pdf.js / SyncTeX requirement).  
- Lint → diagnostics rail.  
- Download PDF and `.tex` when source exists.

### 5.8 Score

- Manual async job: queued → processing → complete | failed.  
- Overall + categories + evidence; optional `jd_match`.  
- Engines: `hiring_agent` or `stub`.  
- GitHub signal from **Settings cache only** (Update GitHub data).  
- Never auto-score after AI edits.

### 5.9 Settings, theme, health

- Settings drawer: email display, GitHub username, Update GitHub data, logout.  
- Light/dark with diagonal wipe; honor reduced motion.  
- Health endpoint reports score/latex backends (ops).

---

## 6. Scoring contract (product-facing)

- Invocation: async job; progress stepper required.  
- Output includes: overall 0–100, categories (score, evidence, deductions, suggestions), optional jd_match.  
- Re-scoring is **always** manual (“Re-check score”).

---

## 7. Technology (high level — implementation guidance)

| Layer | Choice |
|-------|--------|
| API | FastAPI, REST `/api/v1` |
| UI | React + Vite + TypeScript + Tailwind |
| DB | SQLite |
| Auth | Email + password, JWT |
| Files | Local object store (S3-shaped seam later) |
| Jobs | In-process runner for score |
| PDF | Tectonic preferred; layout fallback |
| Score | hiring_agent or stub |
| LLM (generate) | ollama · openrouter · groq · stub |
| Preview | Browser iframe |
| Editor | CodeMirror-style LaTeX |

Modular seams: scoring, compile, auth, jobs independently replaceable. Prefer minimal code (ponytail): no new deps if stdlib/existing stack covers it.

---

## 8. Explicitly out of scope (not current MVP)

Label these **future** if implemented later—**do not** require them for “done”:

| Item | Why |
|------|-----|
| User template marketplace / primary picker | Templates are internal generate skill reference only |
| PDF/DOCX upload → extract as primary create | Not shipped CTA |
| GitHub OAuth + live fetch every score | Cache refresh only |
| Subscription tiers / resume limits UI | Not present |
| Cloud multi-tenant hosting productization | Local-first MVP |
| SyncTeX / pdf.js viewer | Removed from current product |
| Teams, shared resumes, monetization | Not shipped |

---

## 9. Non-functional / trust

- Sanitize JD and applied edits; fence untrusted content for models.  
- User-owned data isolation.  
- No secrets in repo; env-based keys for cloud LLMs.

---

## 10. Acceptance script (product done)

1. Register → login → theme toggle.  
2. Settings: GitHub username → Update GitHub data → cache status.  
3. New AI resume → Form|Source → AI Generate → AI **or** template fallback toast → **source-only** (track latex; no Form; no AI Generate) → PDF.  
4. Compile / Lint / download PDF and .tex.  
5. Check score (± JD) → stepper → overall + categories.  
6. Version commit → restore → delete.  
7. New LaTeX: no Form from the start.  
8. List search, tags, delete; post-generate track latex on list.  
9. No primary template picker.

---

## 11. Doc map

| Depth | Doc |
|-------|-----|
| Contract | this PRD |
| Feature behavior | [`docs/product/`](./docs/product/README.md) |
| Agent rules | [`AGENTS.md`](./AGENTS.md) |
| Build order | [`PLAN.md`](./PLAN.md) |

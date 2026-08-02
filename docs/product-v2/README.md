# ResumeAI product docs (v2 — improved rebuild bible)

**Edition:** improved structure for rebuild-from-scratch  
**Product state documented:** **current shipped** behavior (same product as [`docs/product/`](../product/README.md))  
**What is better vs original:** [`WHAT_CHANGED.md`](./WHAT_CHANGED.md)

> Original/current set is **preserved** at `docs/product/`. This folder is a second, clearer edition—not a different product.

---

## Top rebuild traps (read first)

Do **not** rebuild these as if they ship today:

| Trap | Shipped truth |
|------|----------------|
| User-facing **template picker** as create UX | Only **New AI resume** + **New LaTeX** |
| **Free-form coach chat** | **Fixed actions only** |
| **Permanent Form \| Source** after New AI generate | Generate → track **`latex`** → **source-only** (Form + **AI Generate** gone) |
| **Auto-score** after coach apply / generate | Manual **Check / Re-check score** only |
| **Live GitHub API** on every score | **Settings cache** only (**Update GitHub data**) |
| Silent generate that *looks* like AI | Surface **`used_llm`**: **AI** vs **template fallback** |
| pdf.js / SyncTeX preview stack | Browser **iframe** + PDF blob |
| PDF/DOCX extract as primary create | Not a list CTA |

Full out-of-scope list: [11 — Constraints](./11-constraints-and-out-of-scope.md).

---

## Rebuild in one page

### Workspace modes (state machine)

```
New AI resume
  └─ Mode FORM_PATH (track = structured)
        Form | Source tabs · AI Generate visible · fill form
        └─ AI Generate (success)
              └─ Mode LATEX_ONLY (track = latex)
                    Source only · no Form · no AI Generate
                    coach / score / versions / compile …

New LaTeX
  └─ Mode LATEX_ONLY from the start (track = latex)
```

| Mode | Track chip | Editor chrome | AI Generate |
|------|------------|---------------|-------------|
| **FORM_PATH** | `structured` | Form \| Source | Yes |
| **LATEX_ONLY** | `latex` | LaTeX source only | No |

Legacy exception: resume with template id may keep form chrome after generate—**not** the primary create flow.

### Journey A — AI resume (primary)

1. Register (email + password ≥ 8) → auto-login → Resumes.  
2. Optional: Settings → GitHub username → **Update GitHub data**.  
3. **New AI resume** → Mode **FORM_PATH**.  
4. Fill form (basics, work, education, skills, projects, …) → Save.  
5. **AI Generate** → toast **AI** or **template fallback** → Mode **LATEX_ONLY**.  
6. Compile / auto-preview → PDF.  
7. Optional JD in coach → **Check score** → queued → processing → complete.  
8. Coach fixed action → select hunks → **Apply selected** → recompile.  
9. Versions **Commit**; download **PDF** / **.tex**.  
10. **Re-check score** only when user chooses (never auto after apply).

### Journey B — Own LaTeX

1. **New LaTeX** → Mode **LATEX_ONLY** immediately.  
2. Edit source → Compile / Lint / Score / Coach / versions / downloads.

### Journey C — Day-to-day multi-resume

Search, tag filter, open, delete with confirm; edit title/tags on identity row.

### Path guides

| Rebuilding… | Read in order |
|-------------|----------------|
| Journey A | [02 Create](./02-resumes-list-and-create.md) → [04 Form](./04-form-source-editor.md) → [05 Generate](./05-ai-generate.md) → [03 Workspace](./03-workspace.md) → [08 Compile](./08-compile-pdf-lint-downloads.md) → [09 Score](./09-score.md) → [06 Coach](./06-coach.md) |
| Journey B | [02 Create](./02-resumes-list-and-create.md) → [03 Workspace](./03-workspace.md) → [04 Editor (source)](./04-form-source-editor.md) → [08](./08-compile-pdf-lint-downloads.md) → [09](./09-score.md) → [06](./06-coach.md) |
| Auth / shell | [01 Auth](./01-auth-and-session.md) → [10 Settings & theme](./10-settings-github-theme.md) |
| Correctness gate | [11 Constraints](./11-constraints-and-out-of-scope.md) |

### Acceptance script (product “done”)

1. Register → login → theme toggle.  
2. Settings: GitHub username → Update GitHub data → cache status.  
3. New AI resume → form (Form\|Source) → AI Generate → **AI** or **template fallback** toast → **source-only** (track **latex**, **no** Form tab, **no** AI Generate) → PDF.  
4. Compile / Lint / download PDF and .tex.  
5. Check score (± JD) → stepper → overall + categories.  
6. Coach → Apply selected → PDF updates → score **unchanged** until Re-check.  
7. Version commit → restore → delete checkpoint.  
8. New LaTeX: no Form tab from the start.  
9. List search, tags, delete; post-generate row shows track **latex**.  
10. No free-form chat; no primary template picker.

---

## What ResumeAI is

Local-first workspace for engineers to:

1. Own many resumes (form → AI LaTeX, or paste LaTeX).  
2. Compile to PDF (tectonic preferred; layout fallback).  
3. Score with ATS-style engine (hiring-agent or stub), optional JD, **cached** GitHub.  
4. Coach via **fixed actions** and approve-to-apply find/replace hunks.

SaaS-shaped seams (auth, jobs, storage); MVP runs on one machine.

---

## Technology (high level only)

| Layer | Choice |
|-------|--------|
| API | FastAPI, REST `/api/v1` |
| UI | React + Vite + TypeScript + Tailwind |
| DB | SQLite |
| Auth | Email + password, JWT in browser storage |
| Files | Local object store |
| Jobs | In-process runner (score) |
| PDF | Tectonic preferred; layout fallback |
| Score | `hiring_agent` or `stub` |
| LLM | ollama · openrouter · groq · stub |
| Preview | Browser iframe + blob (no pdf.js / SyncTeX) |
| Editor | CodeMirror-style LaTeX |

Health: `GET /api/v1/health` → score/latex/coach backends.

---

## Feature index

| Doc | Covers |
|-----|--------|
| [01 — Auth & session](./01-auth-and-session.md) | Register, login, session, logout |
| [02 — List & create](./02-resumes-list-and-create.md) | Multi-resume, New AI / New LaTeX, search/tags |
| [03 — Workspace](./03-workspace.md) | Two-tier chrome, control catalog, rail · editor · PDF |
| [04 — Form & source editor](./04-form-source-editor.md) | Form fields, modes, dirty, highlights |
| [05 — AI Generate](./05-ai-generate.md) | Generate pipeline, used_llm, track flip |
| [06 — Coach](./06-coach.md) | Fixed actions, hunks, apply |
| [07 — Versions](./07-versions.md) | Commit / restore / delete |
| [08 — Compile, PDF, lint, downloads](./08-compile-pdf-lint-downloads.md) | Engines, preview, lint, .pdf/.tex |
| [09 — Score](./09-score.md) | Async job, categories, GitHub cache |
| [10 — Settings, GitHub, theme](./10-settings-github-theme.md) | Drawer, cache refresh, light/dark wipe |
| [11 — Constraints & out of scope](./11-constraints-and-out-of-scope.md) | Hard rules, PRD-only gaps |
| [WHAT_CHANGED](./WHAT_CHANGED.md) | Deltas vs `docs/product/` |

**Companions:** root [README](../../README.md) (run/env), [LESSONS](../../LESSONS.md), [PRD](../../PRD.md) (**vision only**).

---

## Document maintenance

- Shipped behavior change → update **both** `docs/product/` (if still maintained as original snapshot policy) and **this** v2 set, plus root Features table. Prefer v2 for new rebuild readers.  
- Product-intent mistakes → `LESSONS.md`.

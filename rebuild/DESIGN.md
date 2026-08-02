# DESIGN.md — ResumeAI structure (current app)

**Scope:** Information architecture and screen structure only — **no visual design, tokens, motion, or taste**.  
**Source of truth for this file:** live rebuild app, captured with Playwright against `http://127.0.0.1:5173` (API `:8001`), plus `frontend/src` chrome rules.  
**Supersedes:** [`OLD-DESIGN.md`](./OLD-DESIGN.md) (previous visual design system; outdated chrome assumptions).  
**Product rules (behavior):** [`docs/product/`](./docs/product/README.md) + [`PRD.md`](./PRD.md). Where product docs describe features not yet in this tree (e.g. AI Generate pivot), this file documents **what the UI actually renders today**.

Captured screens: login · register · empty list · list with rows · workspace FORM_PATH · workspace LATEX_ONLY · settings drawer.

---

## 1. Routes and shells

| Path | Auth | Shell | Primary component |
|------|------|-------|-------------------|
| `/login` | guest | `main.shell.auth` | `AuthScreen` (login) |
| `/register` | guest | `main.shell.auth` | `AuthScreen` (register) |
| `/` | session | `main.shell.wide` | `ResumesHome` |
| `/resumes/:id` | session | `main.workspace` | `Workspace` |
| any + Settings | session | overlay on current shell | `SettingsDrawer` |

Client guards: unauthenticated users land on login; authenticated users cannot stay on auth routes. `?settings=1` opens the drawer once, then cleans the query.

```
Guest                         Session
  /login  ⇄  /register          /  (list)
       \                      /  \
        \── success ────────→     └─ /resumes/:id  (workspace)
                                      Settings drawer (overlay, any session screen)
```

---

## 2. Auth (`/login`, `/register`)

```
┌ main.shell.auth ─────────────────────────────────────┐
│ header.auth-head                                      │
│   h1 ResumeAI                                         │
│   muted: "Sign in" | "Create account"                 │
│   [ThemeToggle]                                       │
│                                                       │
│ form.card                                             │
│   Email     [ input type=email ]                      │
│   Password  [ input type=password ]                   │
│             (register label: "Password (≥ 8)")        │
│   [ Continue | Create account ]                       │
│                                                       │
│ footer-link                                           │
│   Need an account? [Create one]                       │
│   Already have an account? [Log in]                   │
└───────────────────────────────────────────────────────┘
```

| Control | Login | Register |
|---------|-------|----------|
| Submit | Continue | Create account |
| Switch | Create one → `/register` | Log in → `/login` |
| Success | session + navigate `/` | auto-login + `/` |

No other fields. Theme toggle is present on auth.

---

## 3. Resume list (`/`)

```
┌ main.shell.wide ──────────────────────────────────────┐
│ header.row                                            │
│   h1 Your resumes                                     │
│   muted count / empty copy                            │
│   header-actions: [ThemeToggle] [Settings] [Log out]  │
│                                                       │
│ cta-row                                               │
│   [ New resume ]   [ New LaTeX ]     ← only create CTAs │
│                                                       │
│ filters.card                                          │
│   Search [ title / track / tag text ]                 │
│   [ Add tag filter input ] [Add tag] [Clear filters?] │
│   selected tag chips (click removes)                  │
│   muted: "Tags in results: …" when any                │
│                                                       │
│ empty: card.empty instructions                        │
│   OR                                                  │
│ list: ul.resume-list                                  │
│   li.resume-row × N                                   │
│     [title link]  track-chip  tags  [Delete]          │
└───────────────────────────────────────────────────────┘
```

### Create CTAs (hard structure)

| Button label (live) | Create kind | Opens as |
|---------------------|-------------|----------|
| **New resume** | `ai` / form path | track `structured`, FORM_PATH workspace |
| **New LaTeX** | `latex` | track `latex`, LATEX_ONLY workspace |

No template picker, no third create button, no “from upload” CTA.

### List row contents

- Title (opens `/resumes/:id`)
- Track chip: `structured` | `latex`
- Tags text or `—`
- Delete (confirm)

---

## 4. Workspace modes (chrome matrix)

Derived from `workspaceMode.ts` / live DOM:

| Mode | Track chip | Editor label | Form body | Source textarea | Lint in Build | Diagnostics in rail |
|------|------------|--------------|-----------|-----------------|---------------|---------------------|
| **FORM_PATH** | `structured` | static **Form** | yes | no | no | no |
| **LATEX_ONLY** | `latex` | static **LaTeX source** | no | yes | yes | yes |

There is **no** Form | Source dual tab in the live tree: each mode shows a single static editor label. There is **no** AI Generate control in the live toolbar.

```
New resume  →  track structured  →  FORM_PATH
New LaTeX   →  track latex       →  LATEX_ONLY
```

---

## 5. Workspace shell (both modes)

Common chrome for `/resumes/:id`:

```
┌ main.workspace ───────────────────────────────────────────────────┐
│ identity-row (tier 1)                                             │
│   [← Resumes] [Settings] [ThemeToggle]                            │
│   [title input]  track-chip  engine-chip  dirty/saved-chip        │
│   [tags input]                                                    │
│                                                                   │
│ toolbar role=toolbar "Workspace actions" (tier 2)                 │
│   File   | Build              | Score         | Danger            │
│   Save   | Compile            | Check score   | Delete            │
│   .tex   | [Lint if LATEX] PDF| (→ Re-check…) |                   │
│                                                                   │
│ status-line (ok | err) · ToastHost                                │
│                                                                   │
│ workspace-grid                                                    │
│   aside.rail  |  section.editor  |  aside.pdf-pane                │
└───────────────────────────────────────────────────────────────────┘
```

### 5.1 Identity row

| Element | Role |
|---------|------|
| ← Resumes | back to list |
| Settings | open drawer |
| ThemeToggle | light/dark |
| title input | resume title (`aria-label="Resume title"`) |
| track-chip | `structured` or `latex` |
| engine-chip | compile engine after first compile, else `—` |
| dirty/saved-chip | `Unsaved` / `Saved` |
| tags input | comma-separated tags |

### 5.2 Toolbar groups

| Group (`data-group`) | Controls | Notes |
|----------------------|----------|-------|
| **File** | Save, .tex | `.tex` disabled until a LaTeX snapshot exists |
| **Build** | Compile, **Lint** (LATEX_ONLY only), PDF | Lint absent from DOM on FORM_PATH |
| **Score** | Check score → Re-check score after first complete | Manual only; never auto |
| **Danger** | Delete | confirm |

### 5.3 Grid columns

| Region | `aria-label` | Always | Conditional |
|--------|--------------|--------|-------------|
| Left rail | Left rail | Versions, ATS score | Diagnostics (LATEX_ONLY) |
| Center editor | Editor | mode label + body | Form vs source |
| Right PDF | PDF preview | heading + empty/busy/iframe | PDF after Compile |

---

## 6. FORM_PATH workspace (track `structured`)

Live tree (Playwright `04-workspace-form`):

```
┌ Identity · track structured · engine — · Saved · tags ───────────┐
│ File: Save .tex | Build: Compile PDF | Score: Check score | Danger │
├───────────────┬────────────────────────────┬──────────────────────┤
│ rail          │ editor                     │ pdf-pane             │
│               │ tabs: [Form] (static)      │ PDF                  │
│ Versions      │ structured-form            │ empty → Compile      │
│  [msg] Commit │  Basics (fields)           │ or iframe blob       │
│  list / empty │  Work / Education /        │                      │
│               │  Projects / Skills         │                      │
│ ATS score     │  (↑↓ reorder, Add/Remove)  │                      │
│  Queued→…     │                            │                      │
│  (no Lint)    │  NO source · NO Generate   │                      │
└───────────────┴────────────────────────────┴──────────────────────┘
```

### Form sections (order from `section_order`)

1. **Basics** (fixed head): Name, Email, Phone, Location, Website/portfolio, LinkedIn, GitHub, Summary  
2. **Work** — Company, Position, Dates, Summary (+ Add / Remove / ↑↓)  
3. **Education** — Institution, Area, Degree, Dates  
4. **Projects** — Name, URL, Description, Highlights  
5. **Skills** — Name, Keywords  

Section and entry reorder via ↑ / ↓. Compile keeps the form editable (status: form still editable).

---

## 7. LATEX_ONLY workspace (track `latex`)

Live tree (Playwright `07-workspace-latex`):

```
┌ Identity · track latex · engine — · Saved · tags ────────────────┐
│ File: Save .tex | Build: Compile Lint PDF | Score | Danger        │
├───────────────┬────────────────────────────┬──────────────────────┤
│ rail          │ editor                     │ pdf-pane             │
│ Versions      │ tabs: [LaTeX source]       │ PDF                  │
│ Diagnostics   │ source-editor-shell        │ iframe after compile │
│  (Lint fills) │   textarea LaTeX source    │                      │
│ ATS score     │ NO Form · NO Generate      │                      │
└───────────────┴────────────────────────────┴──────────────────────┘
```

Differences vs FORM_PATH (structure only):

- Build includes **Lint**
- Rail includes **Diagnostics** section
- Editor is monospace source only (starter `\documentclass…` on create)
- Default title often “LaTeX resume”

---

## 8. Left rail detail

### Versions

```
Versions
  [ checkpoint message input ]  [Commit]
  empty: "No checkpoints yet."
  OR list of rows: message · time · [Restore] [Delete]
```

### Diagnostics (LATEX_ONLY only)

```
Diagnostics
  empty: "Run Lint for issues and fix hints."
  OR list: severity · optional L{n} · message (click may set status jump)
```

### ATS score

```
ATS score
  ol stepper: Queued → Processing → Complete  (Failed on complete step if failed)
  idle copy: "Manual Check score only — never auto after edits."
  result: overall /100 · category list · optional weak-GitHub hint → Settings
```

Not a unified “compile ledger” transcript: three **separate** rail sections (Versions / Diagnostics / ATS).

---

## 9. PDF pane

```
PDF
  busy: "Updating…"
  empty: "Click Compile for iframe preview (blob URL; no pdf.js)."
  ready: iframe.title="Resume PDF preview"  (blob URL)
```

No SyncTeX, no pdf.js requirement.

---

## 10. Settings drawer

Opened from list or workspace. Overlay `settings-overlay` + dialog `settings-drawer`.

```
┌ Settings ────────────────── [✕] ─┐
│ Account                           │
│   email                           │
│   note: contact links on form     │
│                                   │
│ GitHub (for scoring)              │
│   username [ ]                    │
│   [Save username]                 │
│   [Update GitHub data]            │
│   cache status line               │
│                                   │
│ [Log out]                         │
└───────────────────────────────────┘
```

Theme is **not** inside Settings (lives on shell ThemeToggle). Escape or overlay click closes.

---

## 11. Global chrome (all authenticated surfaces)

| Element | Where |
|---------|--------|
| ThemeToggle (`Dark` / `Light`) | auth header, list header-actions, workspace identity-row |
| Settings | list + workspace |
| Log out | list header-actions + Settings drawer |
| ToastHost | list + workspace + settings actions |

---

## 12. Structural absences (do not invent chrome for these)

Documented so redesigns do not reintroduce old or vision-only layout:

| Absent in live DOM | Notes |
|--------------------|-------|
| Template picker / gallery | Create = two CTAs only |
| AI Generate button | Not in toolbar or editor |
| Form \| Source dual tabs | Single static mode label |
| Coach / free-form chat | Not in this rebuild tree |
| Unified compile ledger rail | Versions / Diagnostics / Score are separate panels |
| Theme radios inside Settings | ThemeToggle on shell only |
| pdf.js / SyncTeX UI | iframe + blob only |

---

## 13. Component → file map (structure owners)

| UI region | Source |
|-----------|--------|
| Routes, auth, list | `frontend/src/App.tsx` |
| Workspace chrome + form/source | `frontend/src/Workspace.tsx` |
| Mode matrix | `frontend/src/workspaceMode.ts` |
| Settings drawer | `frontend/src/SettingsDrawer.tsx` |
| Theme toggle | `frontend/src/ThemeToggle.tsx` |
| Toasts | `frontend/src/toast.tsx` |

---

## 14. How this was produced

1. Started rebuild API (`:8001`) + Vite (`:5173`).  
2. Playwright (headless Chromium): register → empty list → **New resume** workspace → Settings → list → **New LaTeX** workspace.  
3. Per screen: interactive inventory (headings, buttons, inputs, landmarks) + simplified DOM tree.  
4. Cross-checked against `Workspace.tsx` / `workspaceMode.ts` for conditional chrome (Lint, Diagnostics, editor body).

To re-capture:

```powershell
# with servers up
cd $env:USERPROFILE\.grok\skills\playwright-skill
node run.js C:\tmp\playwright-structure.js
# output: C:\tmp\resumeai-structure\
```

---

## 15. Relation to OLD-DESIGN.md

| OLD-DESIGN (previous) | Current structure |
|-----------------------|-------------------|
| Visual thesis, tokens, motion | Out of scope for this file |
| Create: “New AI resume” | Live label: **New resume** |
| FORM_PATH: Form \| Source + AI Generate | Form only; no Generate |
| “Compile ledger” as one rail | Versions + Diagnostics + ATS panels |
| Settings includes theme radios | Theme on shell; Settings = account + GitHub + logout |

Use this file for layout / IA work. Use product docs for intended behavior traps. Use OLD-DESIGN only as historical visual reference.

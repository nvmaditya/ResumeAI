# Resume list & create paths

## Purpose

Home base after login: see every resume, create new ones on the **two shipped paths**, search/filter, open the workspace, or permanently delete.

## List screen (“Your resumes”)

**Where:** `/` (authenticated).

### Header

- Title **Your resumes**.
- Subtitle: empty-state guidance *or* count (“N resumes · open one to score, coach, and compile”).
- Primary actions:
  - **New AI resume** (primary button)
  - **New LaTeX** (secondary)

### Search & tags (when at least one resume exists)

- **Search** box filters by title, track name, or tag text (case-insensitive substring).
- **Tag chips** appear for the union of tags across all resumes. Clicking a tag toggles it into an AND filter (resume must include all selected tags).
- **Clear** clears tag filters; empty search + clear filters recovers full list.
- If filters match nothing: card message **No resumes match your filters** + **Clear filters**.

### Resume rows

Each row shows:

- **Title** (link into workspace).
- **Track** chip: **`structured`** for a New AI resume **before** AI Generate; **`latex`** for New LaTeX resumes **and** for New AI resumes **after** a successful generate (track flips—Form chrome goes away; see [AI Generate](./05-ai-generate.md)).
- **Tags** as chips.
- Short id fragment (scannable, not the full UUID focus).
- **Delete** (danger) with confirm: `Delete “{title}”? This cannot be undone.`

### Empty state

When the user has zero resumes:

- Card: **No resumes yet** + short copy about form + AI Generate or paste LaTeX.
- Same two create buttons as the header.

### Errors

- Load failure shows an error line; auth failures redirect to login.
- Create failure shows an error; toast is used on success.

## Create path 1 — New AI resume (primary)

**Intent:** User builds content in a structured form; the system later turns it into LaTeX via **AI Generate**.

**What happens on click:**

1. Creates a resume with a default title like **AI resume**.
2. Track starts as **structured**.
3. Structured JSON is initialized with empty basics (name, email, summary) and empty lists for work, education, skills, projects.
4. Toast: guidance to fill the form, then **AI Generate**.
5. Navigates into the workspace for that resume.

**What does *not* happen:**

- No template gallery.
- No “pick a classic-ats / modern / …” step for the user.
- Internal template assets (if any) are **skill reference only**, not a create-flow picker.

**After AI Generate (same resume):**

- Track becomes **latex**; list chip updates on next load.  
- Workspace is source-only; user does not keep Form + AI Generate on that resume.

## Create path 2 — New LaTeX

**Intent:** User already has or wants raw `.tex` control.

**What happens on click:**

1. Creates a resume titled like **LaTeX resume**.
2. Track **latex**.
3. Seeds a minimal valid document (article class, placeholder body).
4. Toast confirmation; navigates into workspace.

## Delete from list

- Confirm dialog required.
- Permanent; toast **Resume deleted**; list reloads.
- Same destructive idea exists inside the workspace **Danger → Delete** (returns to list).

## Multi-resume

- Unlimited multi-resume in the current MVP (no subscription caps UI).
- Each resume has independent title, tags, source, versions, score jobs, PDF.

## Out of create-flow (do not rebuild as primary UX)

| Idea (often in older PRD) | Current product |
|---------------------------|-----------------|
| “From template” picker | **Not shipped** as primary create |
| Upload PDF/DOCX → extract → edit | Extract may exist as a stub capability; **not** exposed as main list CTA |
| One-resume-only product | Multi-resume is required |

## Rebuild rules

1. Create CTAs are exactly two: **New AI resume** and **New LaTeX**.
2. AI path is form-first; LaTeX path is source-first.
3. List must support search + multi-tag filter + delete confirm.
4. Do not reintroduce a user-facing template chooser as the default create story.

# Form, Source tabs & LaTeX editor

## Two resume editing modes

| Path | How you get there | Editor UX |
|------|-------------------|-----------|
| **Form / AI path (pre-generate)** | **New AI resume** while track is still **structured** (or legacy template-linked resumes) | **Form** and **Source** tabs; **AI Generate** in toolbar |
| **LaTeX-only path** | **New LaTeX**, *or* a New AI resume **after successful AI Generate** (track flips to **latex**) | Source only — **no Form tab, no AI Generate** |

The form path is **not permanent** on the primary New AI flow. See [AI Generate — track flip](./05-ai-generate.md#track-and-workspace-after-generate).

## Structured form (Form tab)

### Purpose

Capture resume content as structured data **before** AI turns it into LaTeX. Contact and career content live **here**, not only in Settings. After a successful generate on the New AI path, the workspace leaves the form chrome; further content work is in **LaTeX source** (coach hunks, manual edits).

### Sections the user can edit

**Basics**

- Name, email, phone, location  
- Website / portfolio, LinkedIn, GitHub  
- Professional summary  

**Lists** (add / remove entries):

| Section | Typical fields |
|---------|----------------|
| Work | Company, position, start/end dates, summary/bullets |
| Education | Institution, area, degree type, dates |
| Skills | Category name + keywords (comma-separated in UI) |
| Projects | Name, description, URL, highlights (one per line in UI) |
| Publications | Name, summary, date |
| Awards | Name, summary, date |
| Certifications | Name, summary, date |

Each list section has **+ Add** and per-card **Remove**.

### Visibility (legacy / template meta)

If a resume still carries internal template metadata, the form may hide fields/sections per that metadata. **New AI resumes** show the full form (all sections). Rebuilds should not depend on a user-facing template picker to unlock fields.

### Form → API shape (product meaning)

- Skills keywords become a list of strings.  
- Project highlights become a list of lines.  
- Empty rows can exist until the user fills them; generate should tolerate sparse data (quality may suffer—that is expected).

## Form | Source tabs

### Rules (critical for current product)

1. While track is **structured** (New AI resume before generate), **both** Form and Source are available.  
2. After **AI Generate** on that path, the product **persists track as `latex`**, reloads the resume, and the workspace becomes **source-only** — Form tab and **AI Generate** disappear. The user does **not** keep a permanent Form|Source dual mode after a normal New AI generate.  
3. Immediately after generate, the UI lands on **Source** so LaTeX is visible (not a form-only dead end).  
4. Coach proposals also keep the user on Source with hunk highlights.  
5. Saving **while still on the form path** persists structured JSON, tags, title, and LaTeX body when present. After the track flip, saves are LaTeX-centric (title, tags, source body).  
6. **Exception (legacy):** resumes that still carry a **template id** may keep their prior track/form chrome after generate; the primary **New AI resume** create flow does **not** set a template id, so the track flip to latex applies.

### Why Form | Source existed before generate

Storing LaTeX while leaving the UI form-only made AI output invisible during the generate moment. Showing Source (and then staying on source-only after track flip) is the shipped fix—not “re-open Form and generate forever.”

## LaTeX source editor

### Capabilities

- Full-document **LaTeX** editing (CodeMirror-style experience).  
- **Syntax coloring** for comments, commands, braces (theme-aware light/dark).  
- **Line numbers**, active line, search keybindings as available in the editor.  
- **Undo / Redo** via toolbar buttons and standard editor history.  
- **Coach hunk decorations**: selected proposed finds highlight strongly; unselected may appear dimmed.  
- **Jump to diagnostic line** from the rail.  
- **Focus hunk**: clicking a proposed diff scrolls/highlights the matching `find` text in source.

### Dirty state

Any edit to form or source marks the resume **Unsaved** until Save (or an action that auto-saves).

### Auto-compile interaction

When source (or form data on form path **after** LaTeX exists) changes, the workspace **debounces** and quietly recompiles for preview. While the user is on Form with **empty** LaTeX, auto-compile is skipped (nothing meaningful to render yet).

## Title & tags (editor-adjacent)

Edited on the identity row; included in save payloads. Tags are free-form labels for list filtering (e.g. `internship`, `faang`).

## Rebuild rules

1. Structured form must cover basics + work + education + skills + projects at minimum; extras (publications/awards/certs) match current product.  
2. Form | Source **only while** the resume is still on the form path (structured / template-linked). After New AI **generate**, track becomes latex → **source-only** chrome (match shipped UI).  
3. Do **not** document “return to Form and generate again” as current behavior on the primary New AI path—that is **not** what ships today.  
4. Source editor must support coach highlight + apply workflow, not only plain text.  
5. Contact links (LinkedIn, portfolio, phone) live on the **resume form** (pre-generate), not Settings—Settings copy should say so.

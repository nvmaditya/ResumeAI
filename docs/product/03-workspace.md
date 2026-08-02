# Workspace chrome

## Purpose

The resume workspace is the main “IDE” for one resume: identity, grouped actions, left rail intelligence, editor, live PDF, and floating coach.

**Where:** `/resumes/:id`.

## Load states

| State | UX |
|-------|-----|
| Loading | Centered “Loading resume…” |
| Failure | Card: **Could not open resume**, error text, **← Back to resumes** |
| Success | Full workspace below |

## Layout (desktop-first)

On wide screens the body is a **three-region grid**:

1. **Left rail** (~3/12) — Versions · Diagnostics · ATS score  
2. **Editor** (~5/12) — Form and/or LaTeX source  
3. **PDF preview** (~4/12) — Browser-native PDF pane  

On narrow screens the regions stack. Overall height fills the viewport under the app header.

Above the grid: **identity row**, **actions toolbar**, optional **status line**.

A **floating Coach** panel is overlaid (see [Coach](./06-coach.md))—not locked into the grid.

## Identity row (tier 1)

Left-to-right product elements:

- **← Resumes** link back to list  
- **Title** input (edits mark dirty)  
- **Track** chip (e.g. structured / latex)  
- **Engine** chip after compile (e.g. tectonic vs layout) when known  
- **Unsaved** chip *or* quiet **Saved** text  
- **Tags** field: comma/semicolon-separated labels (saved with the resume)

This row is **identity and metadata**, not a dumping ground for every action.

## Actions toolbar (tier 2)

Grouped so controls do not compete with title/tags. Groups:

### File

| Control | Role |
|---------|------|
| **Save** | Persist title, tags, form and/or LaTeX body |
| **AI Generate** | Only while form path is active (structured / template-linked); after New AI generate, track is latex and this control is gone |
| **.tex** | Download LaTeX when source exists |

### Build

| Control | Role |
|---------|------|
| **Compile** | Run LaTeX→PDF and refresh preview |
| **Lint** | When source is the active mode; populate diagnostics |
| **PDF** | Download compiled PDF (compiles first if needed) |

### Score

| Control | Role |
|---------|------|
| **Check score** / **Re-check score** | Start async scoring job; label flips after a job has finished once |

### Danger

| Control | Role |
|---------|------|
| **Delete** | Confirm then delete resume and return to list |

Busy states replace labels with short progress (e.g. Generating…, ellipsis on compile/score).

## Status line

A single thin status string under the toolbar for last operation feedback: Saved, compile result + engine, lint counts, score status, generate outcome, applied hunk counts, errors.

Toasts also fire for many of the same events (success and failure).

## Left rail panels

### Versions

See [Versions](./07-versions.md). Commit message + Commit; list of checkpoints with Restore / Delete.

### Diagnostics

Appears when lint or generate produced issues. Each row shows severity, optional line number, message; click jumps to source line.

### ATS score

- Empty: prompt to use **Check score** in the toolbar.  
- Active job: **progress stepper** (queued → processing → complete; failed state separate).  
- Complete: large overall score /100, category list with evidence snippets, optional engine/GitHub/duration meta.  
- Failed: error text.

## Editor column header

- On form path (pre-generate structured): **Form | Source** tabs.  
- On LaTeX-only path (New LaTeX **or** post-generate New AI): label **LaTeX source** — no Form tab.  
- Hint text: form path vs coach-highlight guidance.  
- When source is shown: **Undo / Redo** controls for the editor.

When coach proposals exist and source is visible: **in-editor diff strip** (checkboxes + Apply selected/all + Dismiss) above the editor—mirrored with coach UI.

## PDF column

- Header **PDF preview**; **Updating…** when compile/generate is busy.  
- Empty: guidance to save and compile; notes auto-recompile after a pause.  
- Filled: full-height iframe of the PDF blob.

## Dirty / save discipline (product-level)

Many actions **auto-save if dirty** before proceeding (compile, lint, generate, score, coach, downloads, version commit).  
User still sees **Unsaved** until a successful save clears dirty.

## Rebuild rules

1. Keep **two-tier chrome**: identity separate from File | Build | Score | Danger.  
2. Rail + editor + PDF is the core spatial model; coach floats.  
3. Do not collapse all actions into one wrapping row with tags (that was a rejected UX).  
4. Version rows need scannable message/time and side-by-side Restore/Delete—not cramped stacked-only cells.

# Workspace chrome

## Purpose

Per-resume IDE: identity, grouped actions, left rail, editor, PDF.

**Route:** `/resumes/:id`

## Modes (drives chrome)

| Mode | When | Editor header | AI Generate |
|------|------|---------------|-------------|
| **FORM_PATH** | track `structured` or legacy template id | Form \| Source tabs | Visible |
| **LATEX_ONLY** | track `latex` (New LaTeX **or** post–AI Generate) | “LaTeX source” only | Hidden |

See hub [Workspace modes](./README.md#workspace-modes-state-machine).

## Layout

Wide: **rail (~3)** · **editor (~5)** · **PDF (~4)**. Narrow: stacked.  
Above grid: **identity row** → **toolbar** → optional **status**.

## Identity row (tier 1)

| Element | Role |
|---------|------|
| ← Resumes | Back to list |
| Title input | Rename; marks dirty |
| Track chip | `structured` / `latex` |
| Engine chip | After compile (`tectonic` / layout) |
| Unsaved / Saved | Dirty indicator |
| Tags field | Comma/semicolon tags for list filter |

## Control catalog — toolbar (tier 2)

| Group | Control | When visible | Does |
|-------|---------|--------------|------|
| **File** | Save | Always | Persist title, tags, form and/or LaTeX |
| **File** | AI Generate | **FORM_PATH only** | Form → LaTeX pipeline |
| **File** | .tex | When source exists | Download LaTeX |
| **Build** | Compile | Always (needs source) | LaTeX→PDF + preview |
| **Build** | Lint | LATEX_ONLY or Source tab | Diagnostics rail |
| **Build** | PDF | Always | Download PDF (compile if needed) |
| **Score** | Check / Re-check score | Always | Start async score job |
| **Danger** | Delete | Always | Confirm → delete resume → list |

Many actions **auto-save if dirty** first.

## Left rail

| Panel | Content |
|-------|---------|
| Versions | Commit message + Commit; restore/delete rows |
| Diagnostics | Severity, line, message; click → jump source |
| ATS score | Stepper, overall, categories, errors |

## Outcomes matrix

| Situation | User sees |
|-----------|-----------|
| Loading | “Loading resume…” |
| Load fail | Error card + back to list |
| Dirty | Unsaved chip |
| After action | Status line + often toast |

## Hard rules

1. Two-tier chrome: identity ≠ File\|Build\|Score\|Danger.  
2. AI Generate visibility follows **FORM_PATH** only.  
3. Version rows: message + time + side-by-side Restore/Delete.  
4. Score not auto after edits.

## Done check

- [ ] Toolbar groups match catalog  
- [ ] Post-generate: no AI Generate, no Form tabs  

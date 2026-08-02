# Form, Source & LaTeX editor

## Purpose

Capture structured content **before** generate; edit LaTeX **after** (or from the start on New LaTeX). Support diagnostics jumps.

## Modes

| Mode | Editor UX |
|------|-----------|
| **FORM_PATH** | **Form \| Source** tabs; form is primary content entry |
| **LATEX_ONLY** | Source only — **no Form tab** |

**Critical:** After successful **AI Generate** on New AI path, mode becomes **LATEX_ONLY**. User does **not** keep permanent Form\|Source dual mode and cannot “return to Form and generate again” on that resume (create another New AI resume instead).

## Structured form (Form tab — FORM_PATH only)

### Basics

Name, email, phone, location, website/portfolio, LinkedIn, GitHub, summary.

### Lists (add/remove)

| Section | Fields (typical) |
|---------|------------------|
| Work | Company, position, dates, summary |
| Education | Institution, area, degree, dates |
| Skills | Name + keywords (comma-separated in UI) |
| Projects | Name, description, URL, highlights (lines) |
| Publications / Awards / Certifications | Name, summary, date |

Contact links live **on the form**, not in Settings.

New AI resumes show full form. Legacy template meta may hide fields—implementations must not require a user template picker.

## Source editor (both modes when source shown)

- LaTeX editing with syntax coloring, line numbers, undo/redo.  
- Theme-aware (light/dark same tick as app theme).  
- Jump to diagnostic line.  
- Dirty on any edit until Save / auto-save action.

### Auto-compile

Debounced quiet recompile after edits. Skipped on Form with empty LaTeX.

## Outcomes matrix

| Situation | User sees |
|-----------|-----------|
| New AI, pre-generate | Form tab default-ish; AI Generate available |
| After generate | Source-only; track latex |
| Unsaved edits | Unsaved chip |

## Hard rules

1. Form fields cover basics + work + education + skills + projects (+ extras).  
2. No permanent Form after New AI generate.  
3. Contact fields on form, not Settings-only.

## Done check

- [ ] FORM_PATH vs LATEX_ONLY chrome matches mode table  
- [ ] No “generate again via Form” on primary path  

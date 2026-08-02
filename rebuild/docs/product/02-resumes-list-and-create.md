# Resume list & create paths

## Purpose

Home after login: multi-resume inventory, two create paths, search/filter, open workspace, delete.

## User controls

| Control | Does |
|---------|------|
| **New AI resume** (primary) | Create structured resume → open workspace in **FORM_PATH** |
| **New LaTeX** (secondary) | Create latex resume with starter `.tex` → **LATEX_ONLY** |
| Search | Filter by title, track, or tag text |
| Tag chips | AND-filter by selected tags; Clear tags |
| Row title | Open workspace |
| Delete | Confirm then permanent delete |

## Create path details

### New AI resume

- Default title e.g. **AI resume**.  
- Track starts **`structured`** (Mode **FORM_PATH**).  
- Empty structured JSON (basics + empty lists).  
- Toast guides: fill form, then **AI Generate**.  
- **No** template gallery / picker.

### New LaTeX

- Title e.g. **LaTeX resume**.  
- Track **`latex`** (Mode **LATEX_ONLY** from the start).  
- Minimal valid starter document.  
- No Form tab.

### After AI Generate (same resume)

- Track becomes **`latex`** (see [05](./05-ai-generate.md)).  
- List chip shows **latex** on next load.  
- Workspace is source-only on that resume.

## Outcomes matrix

| Situation | User sees |
|-----------|-----------|
| Zero resumes | Empty card + both create CTAs |
| N resumes | Count subtitle; rows with title, track, tags |
| Filters match none | “No resumes match…” + Clear filters |
| Create success | Toast + navigate to workspace |
| Create fail | Error line |
| Delete | Confirm; toast; list reloads |
| Load fail / unauthenticated | Error or redirect login |

## Hard rules

1. Exactly two primary create CTAs: **New AI resume**, **New LaTeX**.  
2. No user-facing template picker.  
3. Multi-resume supported (no tier caps UI).  
4. Deletes confirm.

## Done check

- [ ] AI-first + LaTeX create only  
- [ ] Search + multi-tag AND filter  
- [ ] Track chip reflects post-generate **latex**  

# Versions (LaTeX checkpoints)

## Purpose

User-driven snapshots of LaTeX: commit, list, restore, delete—without external Git UI.

## Controls

| Control | Does |
|---------|------|
| Commit message | Optional; default **checkpoint**; max ~200 |
| Commit | Save snapshot of current LaTeX (auto-save dirty first) |
| Restore | Confirm → replace live LaTeX → Source → quiet recompile |
| Delete | Confirm → remove checkpoint only |

## Outcomes matrix

| Situation | User sees |
|-----------|-----------|
| No checkpoints | “No checkpoints yet.” |
| Commit with changes | Toast Version saved; list refresh |
| Commit unchanged | “No changes since last commit” |
| Restore | Toast Restored; LATEX_ONLY source |
| Delete | Toast Checkpoint deleted |

## What versions are not

- Not auto on every save.  
- Not full Git branches.  
- Not structured-form history (LaTeX-centric).  
- Restore does not rewrite form JSON to match old LaTeX.

## Hard rules

1. Commit / list / restore / delete all required.  
2. Unchanged detection.  
3. Scannable rows (message + time + actions).  
4. Confirm destructive ops.

## Done check

- [x] Unchanged commit is a no-op toast  
- [x] Restore loads source and recompiles 

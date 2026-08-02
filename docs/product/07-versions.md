# Versions (LaTeX checkpoints)

## Purpose

Let users snapshot the current LaTeX source, browse history, restore an older snapshot, or delete a checkpoint—without an external Git UI.

## Where

Left rail of the workspace, **Versions** panel.

## Commit

**Controls:**

- Message field (placeholder **Commit message**, max ~200 chars).  
- **Commit** button; Enter in the field also commits.

**Behavior:**

1. Auto-saves if the resume is dirty.  
2. Stores a snapshot of current LaTeX with the message (default message **checkpoint** if blank).  
3. If content is identical to the last commit: toast **No changes since last commit** (no duplicate spam).  
4. Otherwise: toast **Version saved**; message field clears; list refreshes.

## Version list

Each row is scannable:

- **Message** (truncated with full title on hover).  
- **Timestamp** (locale string).  
- Actions side-by-side:
  - **Restore** (confirm).  
  - **Delete** (confirm).

Empty state: **No checkpoints yet.**

## Restore

1. Confirm restore of named checkpoint.  
2. LaTeX body replaced with that snapshot.  
3. Dirty cleared; editor switches to **Source**.  
4. Toast **Restored version**.  
5. Quiet recompile for preview.

## Delete checkpoint

1. Confirm delete of that checkpoint message.  
2. Removes only that version (not the live resume).  
3. Toast **Checkpoint deleted**; list reloads.

## What versions are not

- Not a full Git branch model.  
- Not automatic commits on every save (user-driven).  
- Not a structured-form history—checkpoints are **LaTeX-centric**.  
- Restoring does not by itself rewrite the structured form JSON to match old LaTeX.

## Rebuild rules

1. Commit / list / restore / delete are all required.  
2. Unchanged detection avoids no-op commits.  
3. Rows must remain usable (message + time + clear actions)—not a cramped single-column stack of unreadable controls.  
4. Confirm destructive restore/delete.

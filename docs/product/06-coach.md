# Coach (fixed-action AI advisor)

## Purpose

Give score- and JD-aware improvement advice and **concrete find/replace edits** the user explicitly approves. The coach is a **trust-boundary-controlled** surface: the client may only send **whitelisted actions**, never arbitrary chat messages.

## UI shell

- **Floating panel** (draggable; position remembered in the browser).  
- Can **minimize** to a round accent button (bottom-right).  
- Title **Coach**; not a full-page chat transcript product.

## Job description field

- Optional textarea: **Job description (optional)**.  
- Max length **4000** characters (shared with score).  
- Used to ground **Align to JD** and scoring relevance.  
- Input is sanitized server-side (injection patterns filtered; truncated).

## Fixed actions (only these)

| Action id | Button label | Intent |
|-----------|--------------|--------|
| `improve_score` | **Improve score** | Use score evidence/rubric; rephrase existing content for impact; do not invent facts |
| `strengthen_projects` | **Strengthen projects** | Stronger project wording from claims already on the resume |
| `align_jd` | **Align to JD** | Surface truthful keyword alignment with the pasted JD |
| `quantify_impact` | **Quantify impact** | Clarify existing numbers; **never invent metrics**—if none exist, explain in reply only |

While a request runs, buttons show **Working…** and are disabled.

## What the coach returns

1. **Reply** — short natural-language advice (shown in a scrollable snippet).  
2. **Proposed edit** (optional) — section label + list of **hunks**, each hunk a pair:
   - **find** (exact substring expected in current content)  
   - **replace** (new text)

If no hunks: toast **Coach reply ready**.  
If hunks: toast **Coach diffs ready — select in editor**; UI switches to **Source**.

## Per-hunk selection (required UX)

Truncated lists only inside chat are **not** enough. Shipped product requires:

### In the coach panel

- Checkbox per hunk.  
- Truncated −find / +replace preview.  
- Click preview focuses/highlights in the editor.  
- Counter: **selected / total**.  
- **Apply selected (N)** — disabled if none selected.  
- **Apply all**  
- **Dismiss** clears proposal.  
- **Undo src** restores last pre-apply LaTeX backup when available.

### In the editor strip

- Same hunk list with checkboxes when proposals exist and Source is active.  
- **Apply selected / Apply all / Dismiss**.  
- CodeMirror **highlights** selected finds; unselected hunks can appear dimmed.

Default: all hunks start selected when a new proposal arrives.

## Apply behavior

1. User selects a subset (or all).  
2. Server applies only those hunks (exact find required; missing find fails).  
3. LaTeX (or structured field for certain sections) updates and saves.  
4. Toast: applied N hunk(s).  
5. Workspace **recompiles** preview.  
6. If compile fails after apply: **source reverts** to pre-apply content and user is told—protects against broken documents.

**Score is not auto-triggered after apply.** User must manually **Re-check score**.

## Grounding

- Coach is more useful after a completed score (UI copy: “Score first for better advice”).  
- When a complete score job exists, its JSON evidence/suggestions ground advice.  
- Without score, actions still run but with weaker grounding.

## What is forbidden

| Behavior | Status |
|----------|--------|
| Free-form user message box to the model | **Not shipped** |
| Client-invented action strings | Rejected server-side |
| Inventing employers, metrics, links not in the resume | Product rule for model instructions |
| Auto-apply without user approval | Not allowed |
| Auto rescore after apply | Not allowed |

## Rebuild rules

1. Whitelist the four actions; no free-form chat API from the client.  
2. Hunks = find/replace; apply supports **subset**.  
3. Dual surface: coach list + editor strip + source highlights.  
4. Sanitize JD; fence untrusted resume/JD content as data for the model.  
5. Preserve “propose → user selects → apply → optional recompile → manual rescore” loop.

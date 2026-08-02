# Coach (fixed-action advisor)

## Purpose

Score- and JD-aware advice plus **find/replace hunks** the user selects and applies. Trust boundary: **no free-form client messages**.

## Shell

- Floating, draggable panel (position remembered).  
- Minimize to accent FAB.  
- Optional JD textarea (max **4000** chars; sanitized).

## Fixed actions only

| Action | Label | Intent |
|--------|-------|--------|
| `improve_score` | Improve score | Rephrase existing content from score evidence; no invented facts |
| `strengthen_projects` | Strengthen projects | Stronger project wording from claims already present |
| `align_jd` | Align to JD | Surface truthful JD keyword alignment |
| `quantify_impact` | Quantify impact | Clarify existing numbers; **never invent metrics** |

Busy: **Working…** on all actions.

## Returns

1. **Reply** text.  
2. Optional **proposed_edit**: section + hunks (`find` / `replace`).

Toasts: reply ready **or** diffs ready (switch to Source).

## Per-hunk selection (required)

**Coach panel + editor strip + source highlights:**

- Checkbox per hunk; −find / +replace preview.  
- Focus scrolls/highlights in editor.  
- **Apply selected (N)** / **Apply all** / **Dismiss**.  
- **Undo src** restores pre-apply LaTeX backup when available.  
- Default: all hunks selected on new proposal.

## Apply outcomes

| Situation | User sees |
|-----------|-----------|
| Apply success | Toast N hunks; recompile preview |
| Zero selected | “Select at least one hunk” |
| Find missing / validate fail | Apply rejected toast |
| Compile fails after apply | **Source reverts**; explain |

**Score does not auto-run after apply.**

## Outcomes matrix

| Situation | User sees |
|-----------|-----------|
| No score yet | Still can run; copy suggests score first |
| No hunks | Reply only |
| Invalid action string | Rejected server-side |

## Hard rules

1. Whitelist four actions only.  
2. Subset apply supported.  
3. Dual UI + highlights.  
4. Sanitize JD; no invented metrics/employers.  
5. Propose → select → apply → manual rescore.

## Rebuild check

- [ ] No free-form chat box  
- [ ] Apply selected works for subset  

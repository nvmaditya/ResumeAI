# Constraints, rebuild rules & out of scope

Correctness checklist for a from-scratch rebuild of **current** product.

## Non-negotiable constraints

### Trust & AI

1. Coach: four **fixed actions** only—no free-form client chat.  
2. JD/edits sanitized (length, injection filter).  
3. Hunks need explicit user approve; subset apply.  
4. Dual UI: coach + editor strip + highlights.  
5. **No auto-score** after apply/generate.  
6. Generate surfaces **`used_llm`** (AI vs template fallback).  
7. Live generate path when coach backend ≠ stub.

### Create & modes

8. Create CTAs: **New AI resume** + **New LaTeX** only.  
9. No primary user template picker.  
10. **FORM_PATH** only while track structured (or legacy template id). After New AI **generate**, track **`latex`** → **LATEX_ONLY** (Form + AI Generate **gone**). Source must show LaTeX; dual Form\|Source is **not** permanent.  
11. Contact links on resume form (pre-generate).

### Score & GitHub

12. GitHub for scoring = Settings **cache** only.  
13. Async score job + stepper.  
14. Engines: hiring_agent or stub.

### Compile & files

15. Tectonic preferred; non-corrupt layout fallback.  
16. PDF = browser iframe (no pdf.js / SyncTeX requirement).  
17. PDF + .tex downloads when source exists.  
18. Versions: commit / restore / delete + unchanged detection.

### Chrome

19. Two-tier identity + File\|Build\|Score\|Danger.  
20. Rail · editor · PDF · floating coach.  
21. Light/dark wipe; reduced motion.

### Auth

22. Email + password + session; multi-resume; confirm deletes.

## Outcomes to preserve (summary)

| Situation | Behavior |
|-----------|----------|
| Empty list | Both create CTAs |
| Filters empty | Clear filters |
| Auth fail | Inline error |
| Resume load fail | Error + back |
| Generate fallback | Explicit “template fallback” |
| Generate AI | Explicit “AI” |
| Post generate | source-only, track latex |
| Apply 0 hunks | Prompt to select |
| Apply + compile fail | Revert source |
| Score timeout | Try again toast |
| Version unchanged | No-op toast |
| No GitHub cache | Warning; score still possible |

## Out of scope (not current product)

| Item | Note |
|------|------|
| Free-form conversational coach | Trust boundary |
| PDF/DOCX extract as primary create | Not list CTA |
| Template marketplace / picker | Internal skill only |
| GitHub OAuth + live fetch every score | Cache refresh only |
| Subscription tiers | Not present |
| Cloud multi-tenant productization | Local-first MVP |
| SyncTeX / pdf.js | Removed |
| Structured-only forever (no .tex) | .tex download after source exists |
| Monetization / teams | Not shipped |

When `PRD.md` conflicts with this folder or root Features, **this + root README win**.

## Lessons (paraphrased)

1. Live LLM generate on real HTTP path when not stub.  
2. AI generate replaces template-picker create—not beside it.  
3. Per-hunk select + in-editor highlights.  
4. Grouped workspace actions; scannable versions.  
5. After generate, LaTeX visible **and** primary path drops Form chrome (track latex)—lesson “expose Source” means never hide LaTeX, **not** permanent dual tabs.  
6. `used_llm` honesty.

## Acceptance script

Same as [hub](./README.md#acceptance-script-product-done)—definition of product-complete rebuild.

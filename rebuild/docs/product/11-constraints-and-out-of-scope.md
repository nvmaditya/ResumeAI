# Constraints, implementation rules & out of scope

Correctness checklist for implementing **current** product.

## Non-negotiable constraints

### Trust & AI

1. Sanitize JD and edit payloads (length, injection filter).  
2. **No auto-score** after generate.  
3. Generate surfaces **`used_llm`** (AI vs template fallback).  
4. Live generate path when generate backend ≠ stub.

### Create & modes

5. Create CTAs: **New AI resume** + **New LaTeX** only.  
6. No primary user template picker.  
7. **FORM_PATH** only while track structured (or legacy template id). After New AI **generate**, track **`latex`** → **LATEX_ONLY** (Form + AI Generate **gone**). Source must show LaTeX; dual Form\|Source is **not** permanent.  
8. Contact links on resume form (pre-generate).

### Score & GitHub

9. GitHub for scoring = Settings **cache** only.  
10. Async score job + stepper.  
11. Engines: hiring_agent or stub.

### Compile & files

12. Tectonic preferred; non-corrupt layout fallback.  
13. PDF = browser iframe (no pdf.js / SyncTeX requirement).  
14. PDF + .tex downloads when source exists.  
15. Versions: commit / restore / delete + unchanged detection.

### Chrome

16. Two-tier identity + File\|Build\|Score\|Danger.  
17. Rail · editor · PDF.  
18. Light/dark wipe; reduced motion.

### Auth

19. Email + password + session; multi-resume; confirm deletes.

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
| Score timeout | Try again toast |
| Version unchanged | No-op toast |
| No GitHub cache | Warning; score still possible |

## Out of scope (not current product)

| Item | Note |
|------|------|
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
3. Grouped workspace actions; scannable versions.  
4. After generate, LaTeX visible **and** primary path drops Form chrome (track latex)—lesson “expose Source” means never hide LaTeX, **not** permanent dual tabs.  
5. `used_llm` honesty.

## Acceptance script

Same as [hub](./README.md#acceptance-script-product-done)—definition of product-complete implementation.

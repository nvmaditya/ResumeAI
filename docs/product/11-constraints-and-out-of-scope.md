# Constraints, rebuild rules & out of scope

This page is the **correctness checklist** for a from-scratch rebuild that should match current shipped behavior and avoid known product mistakes.

## Non-negotiable product constraints

### Trust & AI surfaces

1. **Coach: fixed actions only** — improve score, strengthen projects, align to JD, quantify impact. No free-form client chat messages.  
2. **JD and edits are sanitized** — length limits; injection-like phrases filtered; untrusted content treated as data for the model.  
3. **Hunks require user approval** — propose → select → apply; never silent overwrite of the whole resume.  
4. **Apply supports subset** of hunks; dual UI (coach + editor strip + highlights).  
5. **No auto-score after coach apply** (or generate)—user re-checks manually.  
6. **Generate honesty** — always surface whether output used a live model (`used_llm`) vs **template fallback**.  
7. **Generate uses real LLM path when configured** — not stub-only in production when a coach backend is set.

### Create & editing model

8. **Two create paths only** as primary UX: **New AI resume** (form → AI Generate) and **New LaTeX**.  
9. **No user-facing template picker** as the main create flow; internal templates/skills are reference for generation quality.  
10. **Form | Source tabs** exist on the AI path **while track is still structured**. After **AI Generate** on a normal New AI resume, track becomes **latex**: Form tabs and AI Generate **disappear**; user continues in source-only. Switch to Source at generate time so LaTeX is visible—do **not** claim permanent dual Form|Source after generate.  
11. Contact links edited on the **resume form** (pre-generate), not only in Settings.

### Scoring & GitHub

12. **GitHub data for scoring comes from Settings cache only** (Update GitHub data).  
13. Score is an **async job** with progress states.  
14. Scoring engines: hiring-agent or stub via configuration.

### Compile & files

15. **Tectonic preferred**; layout fallback allowed; no corrupt fake PDFs.  
16. PDF preview = **browser iframe**, not pdf.js; no SyncTeX requirement.  
17. Downloads: **PDF** and **.tex** where source exists.  
18. Versions: user-driven commit / restore / delete with unchanged detection.

### Workspace UX

19. **Two-tier chrome**: identity row + File | Build | Score | Danger toolbar.  
20. Left rail: versions · diagnostics · score; center editor; right PDF; floating coach.  
21. Light/dark theme with diagonal wipe; honor reduced motion.

### Auth & multi-resume

22. Email + password + session token; multi-resume CRUD with search/tags.  
23. Destructive deletes confirm.

---

## Empty, error, and timeout behaviors to preserve

| Situation | Expected user-visible behavior |
|-----------|--------------------------------|
| Empty resume list | Action-led empty card with both create CTAs |
| Filters match nothing | Clear filters control |
| Login/register failure | Inline error, stay on page |
| Resume load failure | Error card + back to list |
| Compile failure | Toast + status; no corrupt PDF download |
| Generate fallback | Explicit “template fallback” language |
| Generate success with model | Explicit “AI” language |
| Coach without hunks | Reply only + toast |
| Apply with zero selected | “Select at least one hunk” |
| Apply then compile fails | Revert source + explain |
| Score timeout | Toast/status to try again |
| Score failure | Rail error + toast |
| Version unchanged | “No changes since last commit” |
| No GitHub cache | Settings warning; score still possible |
| Unsaved edits | Unsaved chip; many actions auto-save first |

---

## Explicitly out of scope for **current** product

Do **not** document or rebuild these as if they already ship (unless labeled future):

| Item | Notes |
|------|--------|
| Free-form conversational coach | Trust boundary forbids it |
| Primary PDF/DOCX upload → extract create flow | PRD vision; UI is AI form + LaTeX |
| User template marketplace / picker | Templates internal only |
| GitHub OAuth + live fetch every score | Cache refresh only |
| Subscription tiers / resume limits UI | Not present |
| Cloud multi-tenant hosting productization | Local-first MVP |
| SyncTeX / pdf.js preview stack | Removed from current product |
| Structured-only track that never exposes .tex | Current product can download .tex once source exists |
| Monetization, teams, shared resumes | Not shipped |
| Mobile-first redesign | Desktop density is the target |

`PRD.md` remains useful as **future vision** and historical intent. When it conflicts with this folder or root `README.md` Features table, **this folder + README win for “what is built.”**

---

## Lessons that encode product intent

From `LESSONS.md` (paraphrased as rebuild requirements):

1. Wire live LLM generate on the real HTTP path when coach backend ≠ stub.  
2. AI generate replaces template-picker create UX—not “add Generate beside From template.”  
3. Coach hunks need per-hunk select + in-editor highlights.  
4. Workspace actions grouped; versions scannable.  
5. After generate, LaTeX must be visible (Source)—and on the primary New AI path **track becomes latex**, so Form chrome **drops** (source-only thereafter). Historical lesson “Form path exposes Source after generate” means **never leave generated LaTeX invisible**; it does **not** mean permanent Form|Source dual mode after track flip.  
6. `used_llm` honesty in API + toast.

---

## Suggested acceptance script for a rebuild

1. Register → login → theme toggle works.  
2. Settings: set GitHub username → Update GitHub data → cache status shows.  
3. New AI resume → fill form (Form \| Source available) → **AI Generate** → toast **AI** or **template fallback** → LaTeX visible in **source-only** workspace (track **latex**; **no** Form tab; **no** AI Generate button) → PDF previews.  
4. Compile / Lint / download PDF and .tex.  
5. Check score (with and without JD) → stepper → overall + categories.  
6. Coach action → select one hunk → Apply selected → PDF updates → score **unchanged** until Re-check.  
7. Commit version → restore older → delete checkpoint.  
8. New LaTeX path works without Form tab from the start.  
9. List search, tag filter, delete resume; post-generate AI resume shows track **latex** on the list.  
10. Confirm no free-form chat box and no primary template picker.

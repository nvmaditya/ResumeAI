# What changed / what is better (product-v2 vs original)

**Original (preserved):** [`docs/product/`](../product/README.md)  
**Improved:** this folder [`docs/product-v2/`](./README.md)

Both document the **same shipped product**. v2 does not invent features. It reorganizes and hardens the *product bible* so a from-scratch build is less likely to ship the wrong UX.

## Design choices (brainstorm → locked)

| Approach considered | Decision |
|---------------------|----------|
| A. Overwrite `docs/product/` in place | Rejected — originals must remain as the current/original set |
| B. Archive originals, put “canonical” in old path | Rejected — higher risk of confusion for existing links/tests |
| **C. Sibling folder `docs/product-v2/` + explicit WHAT_CHANGED** | **Chosen** — originals untouched; dual discoverability |

**Improvement axes applied:** journey-first entry, first-class workspace **modes/state machine**, uniform empty/error tables, single product acceptance harness, trap callouts for known false implementations, scannable control catalogs.

---

## Concrete deltas (falsifiable)

1. **Originals preserved at a distinct path**  
   - *Before:* one set only under `docs/product/`.  
   - *After:* `docs/product/` unchanged; improved set lives under `docs/product-v2/`.  
   - *Check:* both directories list the full 01–11 topic set; content hashes of originals still match pre-goal baseline.

2. **Journey-first index, not feature-only TOC**  
   - *Before:* TOC of 11 feature files, then journeys mid-page.  
   - *After:* v2 README leads with **Product in one page** (journeys A/B/C + acceptance script), then **workspace modes**, then feature index.  
   - *Check:* v2 `README.md` has a “Product in one page” (or equivalent) section **before** the full feature file table.

3. **First-class workspace mode / state machine**  
   - *Before:* track flip explained inside generate + form docs (easy to miss if you only skim list/create).  
   - *After:* dedicated **Workspace modes** section in the hub + repeated mode badges on form/generate/workspace pages (pre-generate form path vs post-generate latex-only).  
   - *Check:* v2 hub documents modes with pre/post generate chrome; never “Form \| Source after generate” as permanent dual mode.

4. **Uniform “User sees / Empty / Error / Timeout” tables**  
   - *Before:* empty/error UX scattered as prose bullets; density varies by file.  
   - *After:* each major feature doc includes a consistent **Outcomes matrix** (or same-named table) for load/save/fail/timeout.  
   - *Check:* auth, list, generate, score, compile docs each contain an outcomes/empty-error style table.

5. **Single product acceptance harness**  
   - *Before:* acceptance script only in constraints file; easy to skip.  
   - *After:* same script on the v2 hub **and** constraints; hub points to it as the definition of “product done.”  
   - *Check:* v2 README includes numbered acceptance steps including post-generate **source-only** and no Form tab.

6. **Trap callouts (“do not implement as…”) at the hub**  
   - *Before:* out-of-scope mostly at the end of file 11.  
   - *After:* hub has a **Top product traps** box (template picker, permanent Form after generate, auto-score, live GitHub on score, silent generate fallback).  
   - *Check:* those trap phrases appear in v2 README.

7. **Control catalogs (what each button does) in workspace**  
   - *Before:* toolbar groups described, but File/Build/Score/Danger less scannable for implementation checklists.  
   - *After:* workspace doc uses a full control catalog table with **when visible** column (e.g. AI Generate only pre-generate form path).  
   - *Check:* v2 workspace doc lists File/Build/Score/Danger controls with visibility notes.

8. **Cross-links by mode, not only by topic number**  
   - *Before:* linear 01→11 reading order.  
   - *After:* hub links “if implementing the AI path start here → list → form → generate → modes”; LaTeX path skips form/generate.  
   - *Check:* v2 README has explicit path guides for Journey A vs B.

9. **Changelog artifact required**  
   - *Before:* no formal “what’s better” doc.  
   - *After:* this file exists and is linked from v2 README and root README.  
   - *Check:* `docs/product-v2/WHAT_CHANGED.md` present with ≥5 specific bullets (this section).

10. **Accuracy lock language retained and strengthened**  
    - Same shipped truths as original after track-flip fixes: New AI generate → track **latex** → Form + AI Generate **gone**; `used_llm` honesty; GitHub cache-only scoring.  
    - *Check:* in-repo tests assert v2 coverage + track flip + originals still present.

## What deliberately did **not** change

- Product scope (no new features documented as shipped).  
- High-level tech stack choices (FastAPI + React, etc.) — still short tables only.  
- Original files under `docs/product/` (content left as the original/current edition).

## How to choose which set to read

| Need | Use |
|------|-----|
| Historical / original edition used by earlier tests | `docs/product/` |
| Preferred product bible (clearer structure) | `docs/product-v2/` |
| Why v2 exists | this file |

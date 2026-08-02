# AI Generate

## Purpose

One-shot (on primary path) conversion: structured form → full LaTeX document with quality/repair passes. Not free-form chat; not silent background generation on every keystroke.

## When visible

| Resume state | AI Generate |
|--------------|-------------|
| New AI, track **structured** (**FORM_PATH**) | **Yes** |
| After generate, track **latex** | **No** |
| New LaTeX | **No** |
| Legacy template-linked form path | Yes (may keep form chrome) |

## Inputs (product-level)

- Structured form (saved if dirty).  
- Title.  
- Internal generation skill guidance + optional LLM via generate backend (ollama / openrouter / groq).  
- If stub / no live model → **deterministic template-style fallback**.

## Pipeline (behavior)

1. Seed LaTeX (LLM skill-guided or fallback).  
2. Lint/compile-oriented repair loop (order of ~3 iterations).  
3. Persist LaTeX.  
4. Primary New AI path: **set track = `latex`**.  
5. Return status, iterations, diagnostics, **`used_llm`**.

## Honesty: `used_llm`

| Value | Toast language |
|-------|----------------|
| true | **AI** (e.g. generated (AI) · N repair passes) |
| false | **template fallback** |

Silent fallback that looks like live AI is **wrong**.

## Track flip (shipped)

| Before | After success (New AI, no template id) |
|--------|----------------------------------------|
| track `structured` | track `latex` |
| Form \| Source | **Source only** |
| AI Generate button | **Removed** |
| Edit in form then generate | Edit LaTeX; **no** re-generate on this resume |

## Outcomes matrix

| Situation | User sees |
|-----------|-----------|
| Generating | Button **Generating…**; PDF may show busy |
| Success + live model | AI toast; source-only; quiet compile |
| Success + fallback | template fallback toast; same chrome flip |
| Finished with issues | Error/issues toast; partial LaTeX may remain |
| Request hard fail | Failure toast; form data still there (if still FORM_PATH) |

## Hard rules

1. Generate only on form path.  
2. Always surface AI vs template fallback.  
3. Track → latex on primary New AI success; drop Form + AI Generate.  
4. Repair loop required (not one unvalidated dump).  
5. Live generate backend must be able to drive generate in real installs.

## Done check

- [ ] used_llm surfaced  
- [ ] Post-generate chrome = LATEX_ONLY  

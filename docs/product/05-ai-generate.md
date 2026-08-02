# AI Generate

## Purpose

Turn the structured form into a full **LaTeX resume document** the user can compile, coach, version, and download. Generation is a deliberate toolbar action (**AI Generate**), not silent background magic on every keystroke.

## Who sees it

- Visible only while the workspace is on the **form path**: track **structured**, or a legacy resume that still has a **template id**.  
- **Not** shown on pure New LaTeX resumes.  
- **Not** shown after a successful **New AI resume** generate has flipped track to **latex** (button and Form tabs go away).

## Inputs

- Current **structured form** data (saved first if dirty).  
- Resume **title** (used in generation context).  
- Server-side: generation **skill guidance** (internal patterns distilled from quality resume structures) and optional **LLM** via the same coach backend configuration (Ollama / OpenRouter / Groq).  
- If coach backend is **stub** or no live model is available, generation uses a **deterministic template-style fallback** from form fields.

## Pipeline (product behavior, not code)

1. **Seed** LaTeX from form (LLM skill-guided when live; deterministic fallback otherwise).  
2. **Quality / repair loop**: lint structural issues, attempt compile-oriented checks, revise up to a small number of repair passes.  
3. Persist resulting LaTeX on the resume.  
4. On the primary **New AI** path (structured, no template id): **set track to `latex`**.  
5. Return status, iteration count, diagnostics, error (if any), and **`used_llm`**.

Typical cap: a few repair iterations (order of three)—user sees the count in toasts/status.

## Track and workspace after generate

**Shipped behavior (primary New AI resume):**

| Before generate | After successful generate |
|-----------------|---------------------------|
| Track chip: **structured** | Track chip: **latex** |
| Form \| Source tabs | **Source only** (label like LaTeX source) |
| **AI Generate** in File toolbar | **AI Generate removed** |
| Edit content in form, then generate | Edit content in LaTeX; coach hunks; re-generate is **not** offered |

So generate is effectively a **one-shot form → LaTeX conversion** on this path: fill form → AI Generate → work in source thereafter. To run the form flow again, the user creates another **New AI resume** (or would need a product change that is **not** shipped).

**Legacy exception:** if a resume still has a template id, track may stay as-is and form chrome can remain. That is not the create-flow default.

## Honesty: `used_llm`

**Hard product rule:** the UI must tell the user whether a live model wrote the seed or the **template fallback** ran.

| `used_llm` | Toast / status language |
|------------|-------------------------|
| true | **AI** (e.g. “LaTeX generated (AI) · N repair pass(es)”) |
| false | **template fallback** (same pattern with that label) |

Silent fallback that *looks* like a successful AI run is **incorrect product behavior**.

## Outcomes

### Success (`status` ok)

- LaTeX body fills the editor.  
- Diagnostics may still list warnings.  
- UI switches to **Source** (and, after reload, typically **source-only** chrome — see track flip above).  
- Track becomes **latex** on New AI path; identity chip updates.  
- Preview **compiles quietly** after success.  
- Status line summarizes generated · path · ok · iterations.

### Finished with issues

- Toast/status surfaces the error or “issues” message.  
- User still receives whatever LaTeX was produced and can edit/lint manually.  
- `used_llm` honesty still applies.

### Hard failure (request error)

- Toast with failure message; form data remains.

## Busy UX

- Button shows **Generating…** and is disabled while running.  
- PDF pane may show updating/busy while generate+compile chain runs.

## Relationship to templates

- Users do **not** pick a template in create flow.  
- Internal template corpus / generate skill exists so the model (or fallback) produces ATS-sensible structure (section order, contact line, experience layout conventions).  
- Rebuilders should treat templates as **authoring guidance for generation**, not as a multi-step “choose design” product feature.

## Relationship to coach

- Generate creates the initial document.  
- Coach later proposes **hunks** on existing LaTeX.  
- Generate is not free-form chat.

## Rebuild rules

1. Expose **AI Generate** only on the form path (structured / template-linked).  
2. Always surface **AI vs template fallback** from `used_llm`.  
3. After generate on New AI path: persist **track = latex**, show Source, drop Form tabs and AI Generate (match current product).  
4. Include a lint/compile repair loop, not a single unvalidated dump.  
5. When a live coach backend is configured, generation must actually be able to use it—not only unit-test injection paths (product expectation: live env generates with the model).

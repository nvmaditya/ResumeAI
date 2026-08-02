# Design.md — ResumeAI

**Scope:** Visual and interaction design system for the product described in `PRD.md`.
**Applies to:** Phase 3 (workspace shell), Phase 4 (compile/preview), Phase 5 (generate), Phase 7 (score), Phase 9 (polish).
**Does not apply to:** copy for out-of-scope features (§8 of the PRD) — don't design chrome for a template picker or upload-to-extract flow.

---

## 1. Design thesis

ResumeAI turns structured data into a typeset document, and turns that document into a defensible artifact against an ATS. The UI's job is to make an otherwise invisible pipeline — form → LaTeX → compile → PDF → score — legible and trustworthy at every step.

The thesis: **the interface should look like it belongs to the same universe as the document it produces.** A resume is a typeset artifact; a compile is a build; a score is an audit. So the UI borrows its voice from two real crafts, not from generic SaaS: **typesetting** (serif, paper, page) and **the build log** (monospace, ledger, state transitions). Every screen sits somewhere on that spectrum — form and PDF lean typeset, rail and diagnostics lean ledger.

This also gives the product an honesty mechanism for free. `used_llm` isn't a badge, it's a build result — reported the way a compiler reports whether it used the fast path or the fallback. The interface should never oversell what happened; it should log what happened.

**Audience:** software engineers. They're comfortable with monospace, diffs, and state machines, and they'll trust the product more if it looks like a tool built by people who share that taste, not like a consumer resume-builder skinned in gradients.

---

## 2. Token system

### 2.1 Color

Two real themes, not a single palette with an inverted background. Light mode is "paper," dark mode is "terminal." Accent colors are functional — they map to compile/score states, not decoration.

| Token | Light (Paper) | Dark (Ledger) | Use |
|---|---|---|---|
| `--bg-canvas` | `#F6F3EC` (unbleached paper, not cream-white) | `#12151A` (near-black ink) | App background |
| `--bg-surface` | `#FFFFFF` | `#1B1F26` | Cards, panes, editor |
| `--bg-sunken` | `#EDE9DE` | `#0D0F13` | Rail, diagnostics gutter |
| `--ink-primary` | `#1C1B18` | `#EDEAE0` | Body text |
| `--ink-secondary` | `#6B675C` | `#8B8C90` | Labels, captions |
| `--rule` | `#DAD5C7` | `#2A2F38` | Hairlines, dividers |
| `--accent-build` | `#C77F2E` (amber) | `#E0A855` | Queued / compiling / processing |
| `--accent-ok` | `#3E7D53` (muted, not neon) | `#5FAE7A` | Compile success, score pass, `used_llm: true` |
| `--accent-fallback` | `#7A6B45` (dim gold) | `#9A8B5E` | Template fallback (`used_llm: false`) — deliberately *less* celebratory than `--accent-ok` |
| `--accent-error` | `#B0453A` | `#D4685C` | Lint errors, failed jobs, destructive actions |
| `--accent-focus` | `#2F5FA8` | `#6E9FE0` | Keyboard focus ring only — never used decoratively |

Rationale for the pair: warm paper (not cold white, not the common AI-cream/terracotta combo) against true ink-black, so the diagonal theme-wipe (§9.4) reads as "flipping the page over," not a generic dark-mode toggle. Amber/green/gold/red are assigned to *states*, so color becomes information (is this compiling, did it pass, was it a fallback) rather than branding.

### 2.2 Type

Three roles, each borrowed from a real craft:

| Role | Face | Used for |
|---|---|---|
| **Document** | Source Serif 4 (Regular/Semibold) | Resume form field values, PDF-adjacent copy, long-form settings text — anything that reads like the artifact itself |
| **Interface** | Inter (Regular/Medium) | UI chrome: buttons, nav, form labels, toasts, modals — the parts of the screen that are *about* the document, not the document |
| **Ledger** | JetBrains Mono (Regular/Medium) | Track chips, diagnostics, version hashes, score numerals, the compile rail, `used_llm` output — anything reporting a machine state |

Scale (rem, 16px base): `12 / 13 / 15 / 17 / 21 / 28 / 40`. Ledger text never exceeds `15` — it should read like a log, not a headline. Document/body text sits at `15–17`. Only page-level titles (resume title in the identity row) reach `21–28`.

### 2.3 Space, radius, elevation

- Spacing scale: 4 / 8 / 12 / 16 / 24 / 32 / 48px. Workspace grid gutters are 16px; page margins 32px.
- Radius: 2px on ledger/mono elements (chips, diagnostics rows) to read as "typed," 6px on document/interface surfaces (cards, buttons, the PDF pane) to read as "paper." No fully rounded (pill) buttons — pills read as consumer-SaaS default.
- Elevation: one shadow only, used for the PDF sheet against the canvas (`0 12px 32px -12px rgba(0,0,0,0.35)`) so the PDF is the one surface that visually "lifts." Every other panel is flat, separated by `--rule` hairlines, not shadow. Flatness elsewhere makes the PDF's lift meaningful instead of decorative.

---

## 3. Signature element: the compile ledger

The one thing this product should be remembered for: **the left rail doesn't look like a sidebar — it looks like a terminal transcript of the resume's life.**

Instead of a generic icon-list nav, the rail is a single scrolling monospace ledger that appends lines as things happen, oldest at top:

```
 v3   commit  "add SRE role"          2m ago
 v4   commit  "tighten bullets"       just now
 --   lint    2 warnings                    →
 --   build   tectonic · ok            0.8s
 --   score   queued
```

- Versions, diagnostics, and score status are **one rail, one visual language** — not three separate widgets. This is the honest reflection of the PRD's model: they're all just events in one resume's history.
- Each row is clickable: version rows restore, diagnostic rows jump the editor, the score row expands into the stepper.
- New rows append with a short typewriter-style reveal (~120ms per row, not per character) — motion budget spent here, nowhere else in the rail.
- In LATEX_ONLY mode the ledger is identical; only the Form-related rows never appear, because they never happened.

This single element does the work the PRD's "traps" ask for structurally: because versions/diagnostics/score share one transcript, it's visually impossible to fake a "form still exists" state or an "auto-score happened" state — the ledger simply wouldn't have the row.

---

## 4. Layout

### 4.1 Resume list

```
┌──────────────────────────────────────────────────────────┐
│  ResumeAI                                    [☾] [account]│
├──────────────────────────────────────────────────────────┤
│  [ Search title / tag ]        [+ New AI resume] [+ New LaTeX] │
│                                                              │
│  #tag #tag  (AND chips, active = filled, inactive = outline)│
│                                                              │
│  ┌ Card ─────────────┐ ┌ Card ─────────────┐ ┌ Card ────┐  │
│  │ Senior SRE — Acme  │ │ Infra Lead — Beta │ │ + empty  │  │
│  │ [latex]  updated…  │ │ [structured] …     │ │  states  │  │
│  └────────────────────┘ └────────────────────┘ └──────────┘ │
└──────────────────────────────────────────────────────────┘
```

Exactly two creation CTAs, same visual weight, side by side — never a "recommended" or primary/secondary distinction between them, since the PRD treats both journeys as first-class. The track (`[latex]` / `[structured]`) renders as a ledger-style mono chip on the card, not a colored badge — it's a fact being reported, not a status to celebrate.

### 4.2 Workspace — FORM_PATH

```
┌ Identity: title · [FORM_PATH · structured] · dirty • ─────┐
│ File  Build  Score  Danger                                 │
├───────┬──────────────────────────────┬─────────────────────┤
│ ledger│  Form │ Source     (tabs)      │   PDF preview       │
│ rail  │ ─────────────────────────────  │   (paper, shadow)   │
│       │  basics / work / education /   │                     │
│       │  skills / projects / …         │   [Compile]         │
│       │                                 │   [AI Generate]     │
└───────┴──────────────────────────────┴─────────────────────┘
```

`AI Generate` lives in the toolbar, not buried — it's the single most consequential action on this screen (it ends the FORM_PATH mode permanently), so it gets its own button, styled with `--accent-build`, not `--accent-ok` (it hasn't succeeded yet, it's about to run).

### 4.3 Workspace — LATEX_ONLY

```
┌ Identity: title · [LATEX_ONLY · latex] · dirty • ──────────┐
│ File  Build  Score  Danger                                  │
├───────┬──────────────────────────────┬─────────────────────┤
│ ledger│  Source (LaTeX editor, no tabs)│   PDF preview       │
│ rail  │                                │                     │
└───────┴──────────────────────────────┴─────────────────────┘
```

Same shell as 4.2 with the Form tab and the Generate button structurally absent — not hidden via CSS, not grayed out. A disabled ghost button here would silently relitigate the PRD's hard rule ("no Form, no AI Generate"); the component simply isn't in the tree.

### 4.4 Generate result toast

```
┌───────────────────────────────────────────┐
│  ● Generated with AI            [view diff]│
└───────────────────────────────────────────┘
        or
┌───────────────────────────────────────────┐
│  ○ Generated from template fallback         │
│    (AI backend unavailable)      [view diff]│
└───────────────────────────────────────────┘
```

Two visually distinct toasts, not one toast with a footnote. `used_llm: true` uses a filled dot in `--accent-ok`; fallback uses a hollow dot in `--accent-fallback` and states the reason in plain language. Never the same toast shape for both — the PRD's honesty requirement should be visible at a glance, not readable only on close inspection.

### 4.5 Score panel

```
Score            [Check score]  [with JD ▾]
────────────────────────────────────────────
① queued → ② processing → ③ complete
────────────────────────────────────────────
 Overall            78 / 100
 ─ Impact wording    82   ▓▓▓▓▓▓▓▓░░
 ─ JD alignment      71   ▓▓▓▓▓▓▓░░░
 ─ GitHub signal     —    (no cache — set in Settings)
```

Numbered steppers are legitimate here — it's a real, ordered job lifecycle (queued → processing → complete/failed), unlike a decorative "01/02/03" feature list elsewhere. Category bars use `--accent-ok`/`--accent-build`/`--accent-error` by score band, rendered in the Ledger mono face since these are numbers being reported, not prose.

### 4.6 Settings drawer

```
┌ Settings ───────────────────────┐
│ user@email.com          [Logout]│
│ ──────────────────────────────  │
│ GitHub username  [________]     │
│ Cache: updated 3h ago            │
│                [Update GitHub data]│
│ ──────────────────────────────  │
│ Theme   ○ Light  ● Dark          │
└──────────────────────────────────┘
```

"Update GitHub data" is the only button in the app styled as a plain outline (not filled `--accent-build`) — it's a manual refresh, not a build action, and shouldn't visually compete with Compile/Generate/Check score.

---

## 5. Components

- **Track chip** — `[FORM_PATH · structured]` / `[LATEX_ONLY · latex]`, Ledger face, uppercase key / lowercase value, styled like a compiler flag. Always paired — never show mode without track or vice versa.
- **Buttons** — one filled style (`--accent-build` at rest, darkens on press), one outline style for secondary/manual actions, one text-only style for destructive-adjacent-but-reversible (Danger menu items get outline + `--accent-error` border, not filled — filled red is reserved for a final confirm step only).
- **Diagnostics row** — Ledger face, left-aligned severity glyph (`✕` error / `!` warning, not icon-font triangles), click jumps editor to line.
- **Version row** — Ledger face, hash-like short id, commit message in Interface face (it's the one piece of human-authored prose in the rail — deliberately breaks face to stand out).
- **Empty states** — always an instruction, never a mascot or illustration. E.g., resume list empty: *"No resumes yet. Start from a form, or bring your own LaTeX."* — states both real CTAs, promises nothing about a picker.

---

## 6. Voice in error/empty/success states

Per the PRD's honesty requirements, copy follows the ledger's register: state what happened, in the interface's voice, never the user's.

| Situation | Do | Don't |
|---|---|---|
| Compile fails | "Compile failed — tectonic exited with an error. See diagnostics." | "Oops! Something went wrong 😬" |
| Fallback generate | "Generated from template fallback — AI backend unavailable." | "Generated your resume!" (omitting fallback) |
| Score timeout | "Score job timed out. Try again, or check score without a JD." | "This is taking longer than expected..." |
| Version no-op | "No changes since last commit." | "Nothing to save!" |
| GitHub cache stale | "Cache last updated 3h ago." | (silently using stale data with no timestamp) |

---

## 7. Motion

Motion budget is spent in exactly two places, both already required or implied by the PRD:

1. **Theme wipe** — diagonal wipe transition on light/dark toggle (per §5.9), ~400ms, disabled entirely under `prefers-reduced-motion`.
2. **Ledger append** — new rail rows reveal with a ~120ms slide-up-and-settle, staggered if multiple rows land at once (e.g., a commit followed immediately by a recompile).

Everything else — panel switches, tab changes, toasts — is a plain 100–150ms opacity/transform fade. No spinners with personality, no bouncing buttons, no confetti on score completion. A build tool that celebrates itself reads as untrustworthy to this audience.

---

## 8. Accessibility & quality floor

- Keyboard focus ring is `--accent-focus` only, 2px, never the same color as any state accent, so focus is never mistaken for a build/score signal.
- Diagnostics and score bands never rely on color alone — always paired with a glyph or numeral (`✕ 2 errors`, `78/100`, not just a red dot).
- Contrast: body text against `--bg-surface` meets WCAG AA in both themes; Ledger mono at small sizes gets AAA-level contrast since it's frequently the only signal (diagnostics, version hashes).
- PDF iframe and editor both remain usable at 320px width — rail collapses to a toggle drawer below the workspace's two-pane breakpoint (editor + PDF stack vertically first; rail is the first thing to collapse, since it's supplementary to the two primary panes).
- Respect `prefers-reduced-motion` everywhere motion is used (§7), not just the theme wipe.

---

## 9. Anti-patterns (explicitly excluded)

Tied directly to PRD §8 and the "traps" in `PLAN.md` — these are not omissions, they're deliberate exclusions:

- No template gallery/picker chrome, even hidden behind a flag — there is no first-class "browse templates" surface anywhere in this system.
- No single celebratory color/badge for "AI-generated" that would visually flatten the AI-vs-fallback distinction (§4.4).
- No auto-triggered score UI (a "scoring…" state that appears without the user pressing Check/Re-check is a bug against this design, not a feature).
- No decorative numbered-step marketing pattern (01/02/03 feature cards) anywhere outside the score job stepper, which is a real, ordered process.
- No rounded/pill buttons, no cream-and-terracotta or near-black-and-neon default palette — see §2.1 for the deliberate alternative.
# Compile, PDF preview, lint & downloads

## Compile

### Purpose

Turn current LaTeX into a **valid PDF** for preview and download.

### Engines (product-facing)

| Engine | When | Fidelity |
|--------|------|----------|
| **tectonic** | Binary available (bundled path or configured) | Overleaf-like full TeX |
| **layout** fallback | Tectonic missing | Simple layout PDF so preview still works; not full TeX fidelity |

Users see the engine name in the identity **chip** and status line after compile. Health endpoint also reports `latex_engine`.

### Triggers

1. **Compile** toolbar button (manual, with toast).  
2. **Debounced auto-compile** after edits (quiet, no success toast spam).  
3. After successful **AI Generate**, after **restore version**, after successful **coach apply**.  
4. **PDF download** may compile first if no PDF yet.

### Busy / re-entry

- Concurrent compile attempts are ignored while one is in flight.  
- Preview shows **Updating…** when busy.  
- Dirty content is saved before compile when needed.

### Success

- Status: message, optional byte size, engine.  
- Toast (non-quiet): **TeX preview ready** (tectonic) or **Preview ready**.  
- PDF bytes load into the preview pane.

### Failure

- Status + toast with error message.  
- Previous PDF may remain until a successful compile replaces it (rebuilders should not leave corrupt stub PDFs that crash the browser viewer).

## PDF preview

- Browser-native **iframe** + blob URL.  
- **No** pdf.js viewer library.  
- **No** SyncTeX click-to-source mapping in the shipped product.  
- Empty state explains compile; busy state explains rendering.

## Lint

### Purpose

Surface LaTeX issues before or alongside compile so users can fix source.

### When available

- LaTeX-only resumes, or form-path when **Source** tab is active.  
- Toolbar **Lint** (busy ellipsis while running).

### Behavior

1. Save if dirty.  
2. Run lint (may include compile-related checks depending on configuration).  
3. Populate **Diagnostics** in the left rail.  
4. Toast: **No lint issues** or **N lint issue(s)**.  
5. Status: **Lint clean** or count.

### Diagnostics UX

Each diagnostic:

- Severity (**error** vs warning styling).  
- Optional **line** number.  
- Message text.  
- Click → switch to Source and jump to line.

Generate may also attach diagnostics after the repair loop.

## Downloads

### PDF

- Toolbar **PDF**.  
- Ensures a compile exists when needed.  
- File name derived from title (spaces → underscores) + `.pdf`.  
- Toast **PDF download started**.

### LaTeX (.tex)

- Toolbar **.tex** when source exists.  
- Saves if dirty first.  
- Same naming pattern with `.tex`.  
- Toast **LaTeX download started**.  
- Available on LaTeX path and after AI path has produced source (product allows .tex on AI path once LaTeX exists—users can take their source).

## Rebuild rules

1. Prefer tectonic; always have a non-corrupt fallback preview strategy.  
2. Auto-preview after edit is expected; manual Compile remains.  
3. Native PDF iframe is the preview contract.  
4. Lint diagnostics must be actionable (jump to line).  
5. Never ship fake invalid PDF bytes that open as corrupt files.

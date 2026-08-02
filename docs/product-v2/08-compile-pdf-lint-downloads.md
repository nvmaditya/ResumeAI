# Compile, PDF preview, lint & downloads

## Compile

| Engine | When | Fidelity |
|--------|------|----------|
| **tectonic** | Binary available | Full TeX / Overleaf-like |
| **layout** | No tectonic | Simple preview PDF; not full TeX |

Triggers: **Compile** button; debounced auto after edits; after generate / restore / successful coach apply; PDF download if needed.

Busy: ignore re-entry; preview **Updating…**.

## PDF preview

- Browser **iframe** + blob URL.  
- **No** pdf.js, **no** SyncTeX.  
- Empty: guidance to compile; busy: rendering copy.

## Lint

- Available LATEX_ONLY or Source tab on form path.  
- Fills **Diagnostics** rail; jump to line.  
- Toast clean vs N issues.

## Downloads

| Control | Result |
|---------|--------|
| **PDF** | `{title}.pdf` (compile first if needed) |
| **.tex** | `{title}.tex` when source exists (including post–AI generate) |

## Outcomes matrix

| Situation | User sees |
|-----------|-----------|
| Compile success | Status + engine; toast TeX/Preview ready |
| Compile fail | Toast/status error; no corrupt fake PDF |
| Lint clean | “No lint issues” |
| Lint issues | Count + rail list |
| Download | Browser download toast |

## Hard rules

1. Tectonic preferred; non-corrupt fallback.  
2. Auto-preview + manual Compile.  
3. Native iframe preview.  
4. Actionable diagnostics.  
5. Never ship invalid PDF stubs.

## Rebuild check

- [ ] Engine chip/status after compile  
- [ ] Both PDF and .tex downloads work with source  

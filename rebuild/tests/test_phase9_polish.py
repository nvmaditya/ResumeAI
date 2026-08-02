"""
Phase 9 hard rules — theme, outcomes messaging, traps still true.

Product: docs/product/10-settings-github-theme.md, 09-score.md, 07-versions.md, PLAN Phase 9.
"""

from __future__ import annotations

import re
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
FE = WORKSPACE / "frontend" / "src"


def _fe_blob() -> str:
    parts: list[str] = []
    for p in sorted(FE.rglob("*")):
        if p.suffix in (".ts", ".tsx", ".css") and not p.name.endswith(".test.ts"):
            parts.append(p.read_text(encoding="utf-8"))
    return "\n".join(parts)


def test_theme_module_and_toggle_surface() -> None:
    theme = (FE / "theme.ts").read_text(encoding="utf-8")
    assert "prefersReducedMotion" in theme
    assert "toggleTheme" in theme
    assert "resumeai_theme" in theme
    assert (FE / "ThemeToggle.tsx").is_file()
    blob = _fe_blob()
    assert "theme-toggle" in blob
    assert "data-theme" in blob or "dataset.theme" in blob
    assert '"Dark"' in blob or "'Dark'" in blob or ">Dark<" in blob
    assert "bootTheme" in blob


def test_theme_toggle_applies_tokens_immediately() -> None:
    """Product 10: instant token flip same tick; wipe must not delay setTheme."""
    src = (FE / "ThemeToggle.tsx").read_text(encoding="utf-8")
    # Immediate apply on toggle path
    assert "applyThemeToDocument(next)" in src
    assert "setStoredTheme(next)" in src
    assert "setTheme(next)" in src
    # Must not delay setTheme/setStoredTheme behind setTimeout (wipe only)
    delayed = re.findall(
        r"setTimeout\s*\(\s*\(\)\s*=>\s*\{[^}]*setTheme",
        src,
        flags=re.S,
    )
    assert not delayed, f"setTheme must not be delayed: {delayed}"
    delayed_store = re.findall(
        r"setTimeout\s*\(\s*\(\)\s*=>\s*\{[^}]*setStoredTheme",
        src,
        flags=re.S,
    )
    assert not delayed_store, f"setStoredTheme must not be delayed: {delayed_store}"


def test_css_not_corrupted_and_dark_uses_tokens() -> None:
    css = (FE / "index.css").read_text(encoding="utf-8")
    # No PowerShell-style literal newline corruption
    assert "`n" not in css
    assert "}`n" not in css
    # Core chrome must use theme variables (not stuck light hardcodes alone)
    for selector_chunk in (
        ".chip {",
        ".editor {",
        ".tab {",
        ".resume-row {",
        ".structured-form .form-block {",
    ):
        assert selector_chunk in css
    # After .editor { ... } block, expect var(--panel) / var(--border)
    editor_block = re.search(r"\.editor\s*\{([^}]+)\}", css)
    assert editor_block, "missing .editor rule"
    body = editor_block.group(1)
    assert "var(--panel)" in body or "var(--border)" in body
    chip_block = re.search(r"\.chip\s*\{([^}]+)\}", css)
    assert chip_block and "var(--" in chip_block.group(1)
    # Form + LaTeX must theme under dark (no forced #fff form surface)
    form_block = re.search(r"\.structured-form\s*\{([^}]+)\}", css)
    assert form_block, "missing .structured-form"
    assert "var(--panel)" in form_block.group(1)
    form_inputs = re.search(
        r"\.structured-form input,\s*\n\.structured-form textarea",
        css,
    )
    assert form_inputs, "form inputs must share theme rule"
    assert "var(--input" in css or "var(--panel-muted)" in css
    assert "var(--code-bg" in css
    assert "background: #fff" not in re.search(
        r"\.structured-form\s*\{[^}]+\}", css
    ).group(0)
    # Light theme code editor must not force permanent dark IDE colors
    light_block = re.search(
        r"\[data-theme=\"light\"\]\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}",
        css,
        flags=re.S,
    )
    # Tokens are on shared :root,[data-theme=light] block
    root_light = re.search(
        r":root,\s*\[data-theme=\"light\"\]\s*\{([^}]+)\}",
        css,
        flags=re.S,
    )
    assert root_light, "missing light theme token block"
    light_vars = root_light.group(1)
    assert "--code-bg:" in light_vars
    assert "#0f172a" not in light_vars.split("--code-bg:")[1].split(";")[0]
    assert "--code-fg:" in light_vars
    dark_block = re.search(r"\[data-theme=\"dark\"\]\s*\{([^}]+)\}", css, flags=re.S)
    assert dark_block and "#0b1220" in dark_block.group(1).split("--code-bg:")[1].split(";")[0]



def test_reduced_motion_respected_in_css_or_js() -> None:
    css = (FE / "index.css").read_text(encoding="utf-8")
    js = (FE / "theme.ts").read_text(encoding="utf-8") + (
        FE / "ThemeToggle.tsx"
    ).read_text(encoding="utf-8")
    assert "prefers-reduced-motion" in css
    assert "prefersReducedMotion" in js
    assert "theme-wipe" in css and "theme-wipe" in js


def test_score_timeout_message_shipped() -> None:
    ws = (FE / "Workspace.tsx").read_text(encoding="utf-8")
    assert "Score timed out" in ws or "timed out" in ws.lower()
    assert "try again" in ws.lower()
    assert "showToast" in ws


def test_version_unchanged_and_restore_delete_toasts() -> None:
    ws = (FE / "Workspace.tsx").read_text(encoding="utf-8")
    assert "No changes since last commit" in ws or "unchanged" in ws
    # Outcomes matrix: Restored + Checkpoint deleted via toast
    assert "showToast" in ws
    assert re.search(r"showToast\([^)]*Restored|Restored[^;]*showToast", ws) or (
        "Restored" in ws and "showToast(msg" in ws
    )
    assert "Checkpoint deleted" in ws
    # delete path must call showToast near Checkpoint deleted
    del_idx = ws.find("Checkpoint deleted")
    assert del_idx > 0
    window = ws[max(0, del_idx - 200) : del_idx + 200]
    assert "showToast" in window


def test_list_empty_and_filter_empty_outcomes() -> None:
    app = (FE / "App.tsx").read_text(encoding="utf-8")
    assert "No resumes yet" in app or "Create your first resume" in app
    assert "Clear filters" in app
    assert "No resumes match" in app or "match" in app.lower()


def test_phase9_traps_still_true() -> None:
    blob = _fe_blob()
    assert "AI Generate" not in blob
    assert "generateResume" not in blob
    assert "Coach" not in blob
    assert "proposeCoach" not in blob
    assert "From template" not in blob
    assert "New resume" in blob
    assert "New LaTeX" in blob


def test_toast_host_for_key_outcomes() -> None:
    assert (FE / "toast.tsx").is_file()
    blob = _fe_blob()
    assert "ToastHost" in blob
    assert "toast-host" in blob

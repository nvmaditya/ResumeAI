"""Workspace mode derivation from track (form-path pivot)."""

from __future__ import annotations

from typing import Any


def workspace_mode_for_track(track: str) -> dict[str, Any]:
    """
    FORM_PATH (structured / New resume): form only; no Source, no Lint.
    LATEX_ONLY (latex): source + Lint.
    """
    t = (track or "").strip().lower()
    if t == "latex":
        return {
            "mode": "LATEX_ONLY",
            "show_form_tab": False,
            "show_source_editor": True,
            "show_lint": True,
        }
    return {
        "mode": "FORM_PATH",
        "show_form_tab": True,
        "show_source_editor": False,
        "show_lint": False,
    }

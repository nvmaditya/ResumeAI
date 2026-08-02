"""Named modular boundaries for health/introspection."""

from __future__ import annotations

# Keep in sync with AGENTS.md modular growth contract
SEAM_NAMES: tuple[str, ...] = (
    "auth",
    "compile",
    "score",
    "jobs",
)

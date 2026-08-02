"""LaTeX checkpoint helpers (pure). Product: docs/product/07-versions.md."""

from __future__ import annotations

DEFAULT_MESSAGE = "checkpoint"
MAX_MESSAGE_LEN = 200


def latex_unchanged(live: str | None, latest_checkpoint_source: str | None) -> bool:
    """True when live source equals latest checkpoint content (byte-for-byte)."""
    return (live or "") == (latest_checkpoint_source or "")


def normalize_message(message: str | None) -> str:
    """Optional message → default checkpoint; trim; max ~200 chars."""
    raw = (message or "").strip()
    if not raw:
        return DEFAULT_MESSAGE
    return raw[:MAX_MESSAGE_LEN]

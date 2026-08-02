"""Structural checks for modular seam packages (shipped code)."""

from __future__ import annotations

from pathlib import Path

from app.seams import SEAM_NAMES


BACKEND = Path(__file__).resolve().parent.parent / "backend" / "app"


def test_seam_packages_exist_on_disk() -> None:
    # Real packages with implementations — no empty protocol-only seams
    for name in ("auth", "compile", "scoring", "jobs"):
        pkg = BACKEND / name
        assert pkg.is_dir(), f"missing seam package: {name}"
        assert not (pkg / "protocol.py").exists(), f"protocol yagni leftover: {name}"


def test_storage_seam_removed() -> None:
    assert "storage" not in SEAM_NAMES
    assert not (BACKEND / "storage").exists()


def test_seam_names_match_contract() -> None:
    assert set(SEAM_NAMES) == {
        "auth",
        "compile",
        "score",
        "jobs",
    }

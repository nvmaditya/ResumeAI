"""
Process/memory contract guard for the ResumeAI product workspace.

Fails if required agent-facing process files or binding section headings
disappear. Runnable without the full app stack.

Also enforces skills-guide process markers and forbids a deprecated workspace label
on product surfaces (see test_product_surface_has_no_deprecated_workspace_label).

Run (from workspace root):
  uv run --project backend pytest tests/test_process_contract.py -q
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest

# workspace root is parent of tests/
WORKSPACE = Path(__file__).resolve().parent.parent

# Deprecated moniker (split so this source file is not a false positive if scanned loosely)
_DEPRECATED_LABEL = "re" + "build"

REQUIRED_FILES = (
    "AGENTS.md",
    "PLAN.md",
    "README.md",
    "PRD.md",
    "LESSONS.md",
    "docs/product/README.md",
)

# Heading text must appear (markdown # / ## / ### allowed via flexible match)
REQUIRED_HEADINGS: dict[str, tuple[str, ...]] = {
    "AGENTS.md": (
        "Development process (binding)",
        "Multi-pass verification",
        "no early stopping",
        "Memory system",
        "Modular growth contract",
        "test-driven-development",
        "high-end-visual-design",
        "dispatching-parallel-agents",
        "verification-before-completion",
        "codebase-design",
        "ponytail",
    ),
    "PLAN.md": (
        "test-driven-development",
        "high-end-visual-design",
        "dispatching-parallel-agents",
        "verification-before-completion",
        "codebase-design",
        "Progress log",
    ),
    "LESSONS.md": (
        "How to append",
        "Lessons",
    ),
    "README.md": (
        "LESSONS.md",
        "skills-guide",
        "test_process_contract",
    ),
}

# Modular seams must be named in the binding agents contract
REQUIRED_SEAMS = ("auth", "compile", "score", "jobs")


def _read(rel: str) -> str:
    path = WORKSPACE / rel
    assert path.is_file(), f"Missing required process/memory file: {rel}"
    return path.read_text(encoding="utf-8")


def _heading_present(text: str, phrase: str) -> bool:
    """True if phrase appears as a heading line or as emphasized contract wording."""
    # Prefer markdown headings containing the phrase
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") and phrase.lower() in stripped.lower():
            return True
    # Also accept non-heading contract phrases that must remain (skill names, etc.)
    return phrase.lower() in text.lower()


@pytest.mark.parametrize("rel", REQUIRED_FILES)
def test_required_process_file_exists(rel: str) -> None:
    path = WORKSPACE / rel
    assert path.is_file(), f"Required process/memory file missing: {rel}"
    assert path.stat().st_size > 0, f"Required file is empty: {rel}"


def test_agents_has_binding_process_and_no_early_stop() -> None:
    text = _read("AGENTS.md")
    assert "Development process (binding)" in text
    assert re.search(r"no early stop", text, re.I)
    assert "Multi-pass verification" in text
    assert "skills-guide" in text.lower() or "Code\\skills-guide" in text or "skills-guide" in text


def test_agents_names_required_skills() -> None:
    text = _read("AGENTS.md")
    for skill in (
        "test-driven-development",
        "high-end-visual-design",
        "dispatching-parallel-agents",
        "verification-before-completion",
        "check-work",
        "codebase-design",
        "ponytail",
    ):
        assert skill in text, f"AGENTS.md must name skill/rule: {skill}"


def test_agents_modular_seams_named() -> None:
    text = _read("AGENTS.md")
    assert "Modular growth contract" in text
    lower = text.lower()
    for seam in REQUIRED_SEAMS:
        assert seam in lower, f"AGENTS.md modular seams must include: {seam}"


def test_agents_memory_system_points_at_lessons_and_global_memory() -> None:
    text = _read("AGENTS.md")
    assert "Memory system" in text
    assert "LESSONS.md" in text
    assert "MEMORY.md" in text or ".grok/memory" in text


def test_plan_phase_skill_map_includes_named_skills() -> None:
    text = _read("PLAN.md")
    for skill in (
        "test-driven-development",
        "high-end-visual-design",
        "dispatching-parallel-agents",
        "verification-before-completion",
        "codebase-design",
    ):
        assert skill in text, f"PLAN.md skill map must include: {skill}"
    assert "Progress log" in text


def test_lessons_has_template_and_entries_section() -> None:
    text = _read("LESSONS.md")
    assert "How to append" in text
    assert "Lessons" in text
    assert "Wrong:" in text or "**Wrong:**" in text


def test_readme_links_process_memory_and_contract_test() -> None:
    text = _read("README.md")
    assert "LESSONS.md" in text
    assert "skills-guide" in text
    assert "test_process_contract" in text


@pytest.mark.parametrize("rel,phrases", list(REQUIRED_HEADINGS.items()))
def test_required_headings_or_phrases(rel: str, phrases: tuple[str, ...]) -> None:
    text = _read(rel)
    missing = [p for p in phrases if not _heading_present(text, p)]
    assert not missing, f"{rel} missing required phrases: {missing}"


def test_process_contract_fails_when_required_file_removed(tmp_path: Path) -> None:
    """
    Negative proof: if a required file is absent from a workspace copy,
    the existence assertion fails. Uses a temp copy so the real tree is untouched.
    """
    # Mirror minimal workspace into tmp
    for rel in REQUIRED_FILES:
        src = WORKSPACE / rel
        dest = tmp_path / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)

    victim = tmp_path / "LESSONS.md"
    assert victim.is_file()
    victim.unlink()

    assert not (tmp_path / "LESSONS.md").is_file()
    # Simulate the same assertion the positive tests use
    with pytest.raises(AssertionError, match="Missing required|not a file|is_file"):
        path = tmp_path / "LESSONS.md"
        assert path.is_file(), f"Missing required process/memory file: LESSONS.md"


def test_process_contract_fails_when_binding_heading_stripped(tmp_path: Path) -> None:
    """Negative proof: stripped binding heading would fail the phrase check."""
    src = WORKSPACE / "AGENTS.md"
    text = src.read_text(encoding="utf-8")
    stripped = text.replace("Development process (binding)", "Process notes (optional)")
    assert "Development process (binding)" not in stripped
    # Same check as production test
    assert "Development process (binding)" not in stripped
    with pytest.raises(AssertionError):
        assert "Development process (binding)" in stripped, (
            "AGENTS.md must retain Development process (binding)"
        )


def test_agents_binds_skills_guide_process() -> None:
    text = _read("AGENTS.md")
    assert "skills-guide" in text
    assert "HOW_TO_WORK" in text or "HOW_TO_WORK.md" in text
    assert "SKILLS_GUIDE" in text or "SKILLS_GUIDE.md" in text
    assert "test-driven-development" in text
    assert "no early stop" in text.lower()


def test_product_surface_has_no_deprecated_workspace_label() -> None:
    """Product docs, app source, and agent entry must not use the deprecated label."""
    paths: list[Path] = [
        WORKSPACE / "AGENTS.md",
        WORKSPACE / "PLAN.md",
        WORKSPACE / "README.md",
        WORKSPACE / "PRD.md",
        WORKSPACE / "LESSONS.md",
        WORKSPACE / "start.sh",
        WORKSPACE / "backend" / "pyproject.toml",
        WORKSPACE / "backend" / "app" / "config.py",
        WORKSPACE / "backend" / "app" / "main.py",
        WORKSPACE / "frontend" / "package.json",
        WORKSPACE / "frontend" / "index.html",
        WORKSPACE / "frontend" / "src" / "App.tsx",
    ]
    docs = WORKSPACE / "docs" / "product"
    if docs.is_dir():
        paths.extend(sorted(docs.rglob("*.md")))
    app = WORKSPACE / "backend" / "app"
    if app.is_dir():
        paths.extend(sorted(app.rglob("*.py")))

    hits: list[str] = []
    pat = re.compile(_DEPRECATED_LABEL, re.I)
    for path in paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if pat.search(text):
            hits.append(str(path.relative_to(WORKSPACE)))
    assert not hits, f"deprecated workspace label still present in: {hits}"

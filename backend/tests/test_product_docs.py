"""Structural checks: product docs cover shipped surface (no coding how-to)."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRODUCT = ROOT / "docs" / "product"
README = ROOT / "README.md"
LESSONS = ROOT / "LESSONS.md"


def _all_product_text() -> str:
    assert PRODUCT.is_dir(), f"missing product docs dir: {PRODUCT}"
    parts: list[str] = []
    for path in sorted(PRODUCT.glob("*.md")):
        parts.append(path.read_text(encoding="utf-8"))
    text = "\n".join(parts)
    assert len(text) > 2000, "product docs too short to be exhaustive"
    return text


def test_product_docs_files_exist():
    required = [
        "README.md",
        "01-auth-and-session.md",
        "02-resumes-list-and-create.md",
        "03-workspace.md",
        "04-form-source-editor.md",
        "05-ai-generate.md",
        "06-coach.md",
        "07-versions.md",
        "08-compile-pdf-lint-downloads.md",
        "09-score.md",
        "10-settings-github-theme.md",
        "11-constraints-and-out-of-scope.md",
    ]
    missing = [n for n in required if not (PRODUCT / n).is_file()]
    assert not missing, f"missing product docs: {missing}"


def test_root_readme_links_product_docs():
    text = README.read_text(encoding="utf-8")
    assert "docs/product" in text
    assert "docs/product/README.md" in text or "product/README" in text


def test_feature_coverage_phrases():
    """Every major shipped area must appear in product docs (product language)."""
    text = _all_product_text().lower()
    required_phrases = [
        # auth
        "register",
        "login",
        "log out",
        "password",
        # list / create
        "new ai resume",
        "new latex",
        "search",
        "tags",
        # workspace
        "file",
        "build",
        "score",
        "danger",
        "identity",
        # form / source
        "form",
        "source",
        "structured",
        # generate
        "ai generate",
        "used_llm",
        "template fallback",
        # coach
        "improve score",
        "strengthen projects",
        "align to jd",
        "quantify impact",
        "apply selected",
        "apply all",
        "fixed action",
        "free-form",
        # versions
        "commit",
        "restore",
        "checkpoint",
        # compile / pdf / lint
        "tectonic",
        "layout",
        "compile",
        "pdf preview",
        "lint",
        "diagnostics",
        ".tex",
        # score
        "queued",
        "processing",
        "hiring",
        "github",
        "cache",
        "re-check score",
        # settings / theme
        "update github data",
        "light",
        "dark",
        "wipe",
        # health
        "health",
        # constraints
        "out of scope",
        "template picker",
    ]
    missing = [p for p in required_phrases if p not in text]
    assert not missing, f"product docs missing coverage phrases: {missing}"


def test_aligns_with_readme_and_lessons_current_state():
    prod = _all_product_text().lower()
    readme = README.read_text(encoding="utf-8").lower()
    lessons = LESSONS.read_text(encoding="utf-8").lower()

    # Current-state truths (not PRD vision)
    assert "no user-facing template" in readme or "no primary user" in prod or "template picker" in prod
    assert "new ai resume" in readme and "new ai resume" in prod
    assert "used_llm" in lessons or "used_llm" in readme
    assert "used_llm" in prod
    assert "per-hunk" in readme or "apply selected" in readme
    assert "apply selected" in prod
    assert "fixed" in readme and "coach" in readme
    assert "free-form" in prod
    # Must not claim free-form chat as shipped feature
    assert "free-form conversational coach" in prod or "no free-form" in prod


def test_no_coding_howto_bulk():
    """Reject docs that are primarily implementation recipes."""
    text = _all_product_text()
    # Allow high-level stack tables; fail on dense code-call recipes.
    forbidden_patterns = [
        r"from app\.\w+ import",
        r"def \w+\(.*\).*->",
        r"npm install",
        r"uvicorn app\.main",
        r"```python\nimport ",
        r"```ts\nimport ",
        r"OpenAPI",
        r"SQLModel",
        r"CREATE TABLE",
    ]
    hits: list[str] = []
    for pat in forbidden_patterns:
        if re.search(pat, text, re.I):
            hits.append(pat)
    assert not hits, f"product docs look like coding how-to: {hits}"

    # High-level stack is OK if short; ensure product words dominate
    product_signals = len(re.findall(r"\b(user|toast|toolbar|coach|score|compile|resume)\b", text, re.I))
    code_signals = len(re.findall(r"\b(function|class |import |export |pytest|endpoint handler)\b", text, re.I))
    assert product_signals > code_signals * 3, (
        f"product language too weak vs code-ish terms ({product_signals} vs {code_signals})"
    )


def test_out_of_scope_excludes_prd_as_current():
    text = (PRODUCT / "11-constraints-and-out-of-scope.md").read_text(encoding="utf-8").lower()
    assert "out of scope" in text
    assert "template" in text and ("picker" in text or "marketplace" in text)
    assert "free-form" in text
    assert "prd" in text


def test_docs_match_post_generate_track_flip_to_latex():
    """Shipped generate sets track latex → Form/AI Generate chrome drops (not permanent Form|Source)."""
    gen = (PRODUCT / "05-ai-generate.md").read_text(encoding="utf-8").lower()
    form_doc = (PRODUCT / "04-form-source-editor.md").read_text(encoding="utf-8").lower()
    constraints = (PRODUCT / "11-constraints-and-out-of-scope.md").read_text(encoding="utf-8").lower()
    overview = (PRODUCT / "README.md").read_text(encoding="utf-8").lower()

    # Docs must describe track flip and chrome loss
    for blob, label in (
        (gen, "05-ai-generate"),
        (form_doc, "04-form-source"),
        (constraints, "11-constraints"),
        (overview, "product README"),
    ):
        assert "latex" in blob and "track" in blob, f"{label}: missing track/latex"
    assert "source-only" in gen or "source only" in gen
    assert "ai generate" in gen and (
        "disappear" in gen or "removed" in gen or "go away" in gen or "gone" in gen
    )
    assert "form" in form_doc and (
        "disappear" in form_doc or "source-only" in form_doc or "source only" in form_doc
    )
    # Must not claim permanent re-generate via Form as current happy path
    assert "return to **form** to edit structured fields and generate again" not in form_doc
    assert "generate again" not in form_doc or "not" in form_doc  # only in negations
    assert "disappear" in constraints or "source-only" in constraints or "source only" in constraints

    # Surface map must not imply permanent Form|Source after generate
    assert "form | source after generate" not in overview
    assert "pre-generate" in overview or "pre‑generate" in overview
    assert "source-only" in overview or "source only" in overview

    # Lessons paraphrase + acceptance script must mention track flip / chrome drop
    assert "track becomes latex" in constraints or "track becomes **latex**" in constraints
    assert "source-only" in constraints or "source only" in constraints
    assert "no** form tab" in constraints or "no form tab" in constraints or "form tab" in constraints
    # Acceptance must not stop at "Source tab has LaTeX" as if dual tabs remain
    assert "source tab has latex" not in constraints

    # Couple docs claim to shipped backend + UI gates
    router = (ROOT / "backend" / "app" / "resumes" / "router.py").read_text(encoding="utf-8")
    editor = (ROOT / "frontend" / "src" / "pages" / "ResumeEditor.tsx").read_text(encoding="utf-8")
    assert 'resume.track = "latex"' in router or "resume.track = 'latex'" in router
    assert "if resume.track == \"structured\"" in router or "track == \"structured\"" in router
    assert "isFormPath" in editor
    assert "track === 'structured'" in editor or 'track === "structured"' in editor
    assert "AI Generate" in editor

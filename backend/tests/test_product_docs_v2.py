"""Structural checks: product-v2 improved docs + originals preserved."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRODUCT = ROOT / "docs" / "product"
PRODUCT_V2 = ROOT / "docs" / "product-v2"
README = ROOT / "README.md"

REQUIRED_TOPIC_FILES = [
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


def _concat(folder: Path) -> str:
    assert folder.is_dir(), f"missing {folder}"
    parts = [p.read_text(encoding="utf-8") for p in sorted(folder.glob("*.md"))]
    text = "\n".join(parts)
    assert len(text) > 2000, f"{folder} docs too short"
    return text


def test_original_product_docs_still_exist():
    missing = [n for n in REQUIRED_TOPIC_FILES if not (PRODUCT / n).is_file()]
    assert not missing, f"originals missing: {missing}"


def test_v2_product_docs_exist_distinct_path():
    assert PRODUCT_V2.resolve() != PRODUCT.resolve()
    missing = [n for n in REQUIRED_TOPIC_FILES if not (PRODUCT_V2 / n).is_file()]
    assert not missing, f"v2 missing: {missing}"
    assert (PRODUCT_V2 / "WHAT_CHANGED.md").is_file()


def test_root_readme_links_both_editions_and_changelog():
    text = README.read_text(encoding="utf-8")
    assert "docs/product/README.md" in text or "docs/product/" in text
    assert "docs/product-v2" in text
    assert "WHAT_CHANGED" in text


def test_what_changed_has_specific_deltas():
    text = (PRODUCT_V2 / "WHAT_CHANGED.md").read_text(encoding="utf-8")
    lower = text.lower()
    assert "docs/product" in lower
    assert "product-v2" in lower or "docs/product-v2" in lower
    # Several numbered concrete deltas
    numbered = re.findall(r"^\d+\.\s+\*\*", text, re.M)
    assert len(numbered) >= 5, f"need ≥5 concrete delta bullets, found {len(numbered)}"
    for needle in (
        "originals preserved",
        "journey-first",
        "workspace mode",
        "outcomes",
        "acceptance",
        "trap",
    ):
        assert needle in lower, f"WHAT_CHANGED missing theme: {needle}"


def test_v2_feature_coverage_phrases():
    text = _concat(PRODUCT_V2).lower()
    required = [
        "register",
        "login",
        "log out",
        "new ai resume",
        "new latex",
        "form_path",
        "latex_only",
        "ai generate",
        "used_llm",
        "template fallback",
        "improve score",
        "strengthen projects",
        "align to jd",
        "quantify impact",
        "apply selected",
        "apply all",
        "fixed action",
        "free-form",
        "commit",
        "restore",
        "checkpoint",
        "tectonic",
        "layout",
        "compile",
        "pdf preview",
        "lint",
        "diagnostics",
        ".tex",
        "queued",
        "processing",
        "hiring",
        "github",
        "cache",
        "re-check score",
        "update github data",
        "wipe",
        "health",
        "out of scope",
        "template picker",
        "source-only",
        "track",
        "outcomes matrix",
    ]
    missing = [p for p in required if p not in text]
    assert not missing, f"v2 missing phrases: {missing}"


def test_v2_no_permanent_form_after_generate():
    overview = (PRODUCT_V2 / "README.md").read_text(encoding="utf-8").lower()
    gen = (PRODUCT_V2 / "05-ai-generate.md").read_text(encoding="utf-8").lower()
    form_doc = (PRODUCT_V2 / "04-form-source-editor.md").read_text(encoding="utf-8").lower()
    assert "form | source after generate" not in overview
    assert "source-only" in overview or "source only" in overview
    assert "latex" in gen and "track" in gen
    assert "removed" in gen or "gone" in gen or "no**" in gen or "hidden" in gen
    assert "generate again" not in form_doc or "not" in form_doc
    # Couple to shipped code
    router = (ROOT / "backend" / "app" / "resumes" / "router.py").read_text(encoding="utf-8")
    editor = (ROOT / "frontend" / "src" / "pages" / "ResumeEditor.tsx").read_text(encoding="utf-8")
    assert 'resume.track = "latex"' in router
    assert "isFormPath" in editor


def test_v2_no_coding_howto_bulk():
    text = _concat(PRODUCT_V2)
    forbidden = [
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
    hits = [p for p in forbidden if re.search(p, text, re.I)]
    assert not hits, f"v2 coding how-to: {hits}"
    product_signals = len(re.findall(r"\b(user|toast|toolbar|coach|score|compile|resume)\b", text, re.I))
    code_signals = len(re.findall(r"\b(function|class |import |export |pytest|endpoint handler)\b", text, re.I))
    assert product_signals > code_signals * 3


def test_v2_hub_has_rebuild_traps_and_acceptance():
    hub = (PRODUCT_V2 / "README.md").read_text(encoding="utf-8").lower()
    assert "rebuild" in hub
    assert "trap" in hub or "traps" in hub
    assert "template picker" in hub
    assert "free-form" in hub
    assert "used_llm" in hub or "template fallback" in hub
    assert "acceptance" in hub
    assert "source-only" in hub or "source only" in hub

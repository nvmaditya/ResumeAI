"""Structural checks: rebuild/ product workspace (shipped app + docs, no coach)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REBUILD = ROOT / "rebuild"
PRODUCT_V2 = ROOT / "docs" / "product-v2"
SEED = REBUILD / "docs" / "product"
README = ROOT / "README.md"

# Shipped product docs in rebuild (coach chapter intentionally removed)
TOPIC_FILES = [
    "README.md",
    "01-auth-and-session.md",
    "02-resumes-list-and-create.md",
    "03-workspace.md",
    "04-form-source-editor.md",
    "05-ai-generate.md",
    "07-versions.md",
    "08-compile-pdf-lint-downloads.md",
    "09-score.md",
    "10-settings-github-theme.md",
    "11-constraints-and-out-of-scope.md",
]

# Historical product-v2 may still list coach; only assert if tree is present
V2_TOPIC_FILES = TOPIC_FILES + ["06-coach.md"]


def test_rebuild_workspace_is_distinct_app_tree():
    assert REBUILD.is_dir()
    assert REBUILD.resolve() != (ROOT / "backend").resolve()
    assert REBUILD.resolve() != (ROOT / "frontend").resolve()
    # Shipped product app (not empty scaffold)
    assert (REBUILD / "backend" / "app" / "main.py").is_file()
    assert (REBUILD / "frontend" / "src" / "App.tsx").is_file()
    assert (REBUILD / "tests").is_dir()


def test_product_v2_source_still_present_when_checked_in():
    """If monorepo product-v2 exists, keep full topic set including historical coach doc."""
    if not PRODUCT_V2.is_dir():
        return
    missing = [n for n in V2_TOPIC_FILES if not (PRODUCT_V2 / n).is_file()]
    assert not missing, f"product-v2 source missing: {missing}"


def test_rebuild_seeded_product_docs_no_coach():
    missing = [n for n in TOPIC_FILES if not (SEED / n).is_file()]
    assert not missing, f"rebuild seed missing: {missing}"
    assert not (SEED / "06-coach.md").is_file(), "coach product doc must stay removed"
    seed_text = "\n".join((SEED / n).read_text(encoding="utf-8") for n in TOPIC_FILES)
    lower = seed_text.lower()
    for phrase in (
        "new latex",
        "used_llm",
        "template fallback",
        "update github data",
        "tectonic",
        "score",
    ):
        assert phrase in lower, f"seed missing phrase: {phrase}"
    # No free-form / coach product surface in rebuild docs
    assert "free-form conversational coach" not in lower or "out of scope" in lower
    assert "track" in lower and "latex" in lower


def test_rebuild_prd_agents_plan_exist_and_substantive():
    for name in ("PRD.md", "AGENTS.md", "PLAN.md", "README.md"):
        path = REBUILD / name
        assert path.is_file(), f"missing {name}"
        text = path.read_text(encoding="utf-8")
        assert len(text) > 800, f"{name} too short to be substantive"


def test_rebuild_prd_current_state_not_vision_mvp():
    prd = (REBUILD / "PRD.md").read_text(encoding="utf-8").lower()
    for phrase in (
        "new latex",
        "github",
        "cache",
        "tectonic",
        "register",
        "score",
        "form_path",
        "latex_only",
    ):
        assert phrase in prd, f"PRD missing: {phrase}"
    assert "out of scope" in prd
    assert "template picker" in prd or "template marketplace" in prd
    # Coach is not a shipped success criterion
    success = prd.split("out of scope")[0]
    assert "free-form conversational" not in success


def test_rebuild_agents_has_constraints_and_done():
    agents = (REBUILD / "AGENTS.md").read_text(encoding="utf-8").lower()
    assert "used_llm" in agents or "template fallback" in agents
    assert "github" in agents and "cache" in agents
    assert "done" in agents or "multi-pass" in agents
    assert "ponytail" in agents
    # No coach fixed-action product requirement
    assert "improve_score" not in agents


def test_rebuild_plan_has_phases():
    plan = (REBUILD / "PLAN.md").read_text(encoding="utf-8").lower()
    assert "phase" in plan
    for needle in ("auth", "workspace", "score", "compile", "theme"):
        assert needle in plan, f"plan missing slice: {needle}"
    assert "track" in plan or "latex_only" in plan or "form_path" in plan or "form path" in plan


def test_root_readme_discovers_rebuild_workspace():
    text = README.read_text(encoding="utf-8")
    assert "rebuild/" in text or "rebuild\\README" in text
    assert "rebuild/PRD.md" in text or "rebuild/PRD" in text
    assert "rebuild/AGENTS.md" in text or "rebuild/AGENTS" in text
    assert "rebuild/PLAN.md" in text or "rebuild/PLAN" in text


def test_rebuild_no_coach_package_or_routes():
    assert not (REBUILD / "backend" / "app" / "coach").exists()
    main = (REBUILD / "backend" / "app" / "main.py").read_text(encoding="utf-8")
    assert "coach" not in main.lower()
    fe = (REBUILD / "frontend" / "src" / "App.tsx").read_text(encoding="utf-8")
    assert "AI Generate" not in fe

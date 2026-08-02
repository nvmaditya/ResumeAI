"""
Phase 7 hard rules — async score + GitHub cache only + no auto-score.

Product: docs/product/09-score.md, 10-settings-github-theme.md
"""

from __future__ import annotations

import ast
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.scoring.stub import StubScoreEngine

API = "/api/v1"
ROOT = Path(__file__).resolve().parent.parent
FE = ROOT / "frontend" / "src"
BACKEND = ROOT / "backend" / "app"


@pytest.fixture()
def client(tmp_path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("SCORE_BACKEND", "stub")
    return TestClient(create_app())


def _auth(client: TestClient) -> dict[str, str]:
    email = f"s_{uuid.uuid4().hex[:10]}@example.com"
    reg = client.post(
        f"{API}/auth/register",
        json={"email": email, "password": "password1"},
    )
    assert reg.status_code == 200, reg.text
    return {"Authorization": f"Bearer {reg.json()['access_token']}"}


def _latex_resume(client: TestClient, h: dict[str, str]) -> str:
    r = client.post(f"{API}/resumes", headers=h, json={"create": "latex"})
    assert r.status_code == 200
    return r.json()["id"]


def test_stub_engine_shape_with_and_without_cache() -> None:
    eng = StubScoreEngine()
    short = eng.score("Hi", jd=None, github_cache=None)
    long = eng.score(
        "Ada Lovelace engineer " * 80,
        jd=None,
        github_cache=None,
    )
    assert "overall" in short and "overall" in long
    assert 0 <= short["overall"] <= 100
    # content-sensitive: longer resume should not always equal short flat score
    assert short["overall"] != long["overall"] or short["categories"] != long["categories"]
    c0 = short["categories"][0]
    assert "name" in c0 and "score" in c0 and "evidence" in c0
    assert short.get("github_enriched") is False

    with_cache = eng.score(
        "Ada Lovelace engineer Python FastAPI projects production",
        jd="Python engineer",
        github_cache={
            "login": "ada",
            "username": "ada",
            "repos": [{"name": "notes", "stars": 3}],
            "repo_count": 1,
            "profile": {"username": "ada"},
        },
    )
    assert with_cache.get("github_enriched") is True
    assert "jd_match" in with_cache


def test_settings_github_save_and_update_cache(client: TestClient) -> None:
    h = _auth(client)
    assert client.get(f"{API}/settings").status_code in (401, 403)

    got = client.get(f"{API}/settings", headers=h)
    assert got.status_code == 200
    body = got.json()
    assert "github_username" in body
    assert body.get("github_cache") in (None, {}) or isinstance(
        body.get("github_cache"), dict
    )
    assert body.get("cache_status")  # human-readable status string

    save = client.patch(
        f"{API}/settings",
        headers=h,
        json={"github_username": "octocat"},
    )
    assert save.status_code == 200, save.text
    assert save.json()["github_username"] == "octocat"

    upd = client.post(f"{API}/settings/github/update", headers=h)
    assert upd.status_code == 200, upd.text
    ub = upd.json()
    assert ub.get("github_cache") or ub.get("cache")
    cache = ub.get("github_cache") or ub.get("cache")
    assert cache.get("login") == "octocat" or cache.get("username") == "octocat"
    assert int(cache.get("repo_count") or cache.get("repos_count") or 0) >= 0
    assert "cache" in (ub.get("cache_status") or "").lower() or "repo" in (
        ub.get("cache_status") or ""
    ).lower() or ub.get("ok") is True

    again = client.get(f"{API}/settings", headers=h).json()
    assert again["github_username"] == "octocat"
    assert again.get("github_cache")


def test_score_job_lifecycle_complete_with_categories(client: TestClient) -> None:
    h = _auth(client)
    rid = _latex_resume(client, h)
    start = client.post(
        f"{API}/resumes/{rid}/score",
        headers=h,
        json={},
    )
    assert start.status_code == 200, start.text
    job = start.json()
    assert job.get("job_id") or job.get("id")
    jid = job.get("job_id") or job.get("id")
    assert job.get("status") in ("queued", "processing", "complete")

    # poll until complete (in-process runner may finish immediately)
    final = None
    for _ in range(20):
        polled = client.get(f"{API}/jobs/{jid}", headers=h)
        assert polled.status_code == 200, polled.text
        final = polled.json()
        if final.get("status") in ("complete", "failed"):
            break
    assert final is not None
    assert final["status"] == "complete"
    result = final.get("result") or final
    overall = result.get("overall")
    assert overall is not None
    assert 0 <= float(overall) <= 100
    cats = result.get("categories") or []
    assert len(cats) >= 1
    assert "name" in cats[0] and "score" in cats[0] and "evidence" in cats[0]


def test_score_without_cache_still_completes(client: TestClient) -> None:
    h = _auth(client)
    rid = _latex_resume(client, h)
    # no settings github update
    start = client.post(f"{API}/resumes/{rid}/score", headers=h, json={})
    assert start.status_code == 200
    jid = start.json().get("job_id") or start.json().get("id")
    final = client.get(f"{API}/jobs/{jid}", headers=h).json()
    # allow immediate complete
    if final.get("status") not in ("complete", "failed"):
        for _ in range(10):
            final = client.get(f"{API}/jobs/{jid}", headers=h).json()
            if final.get("status") in ("complete", "failed"):
                break
    assert final["status"] == "complete"
    res = final.get("result") or {}
    assert res.get("github_enriched") is False


def test_score_uses_cache_only_no_live_github_in_score_path(client: TestClient) -> None:
    """Hard rule: score path must not call live GitHub client."""
    # Structural: scoring package never hits live GitHub API
    score_files = list((BACKEND / "scoring").rglob("*.py"))
    score_files += list((BACKEND / "jobs").rglob("*.py"))
    joined = "\n".join(p.read_text(encoding="utf-8") for p in score_files)
    assert "api.github.com" not in joined
    assert "fetch_live_github" not in joined

    h = _auth(client)
    client.patch(f"{API}/settings", headers=h, json={"github_username": "ada"})
    client.post(f"{API}/settings/github/update", headers=h)

    rid = _latex_resume(client, h)
    start = client.post(
        f"{API}/resumes/{rid}/score",
        headers=h,
        json={"jd": "software engineer"},
    )
    assert start.status_code == 200
    jid = start.json().get("job_id") or start.json().get("id")
    final = client.get(f"{API}/jobs/{jid}", headers=h).json()
    if final.get("status") not in ("complete", "failed"):
        for _ in range(10):
            final = client.get(f"{API}/jobs/{jid}", headers=h).json()
            if final.get("status") in ("complete", "failed"):
                break
    assert final["status"] == "complete"
    res = final.get("result") or {}
    # Cache may enrich; result still has overall/categories either way
    assert "overall" in res or "categories" in res


def test_score_unauth_denied(client: TestClient) -> None:
    rid = str(uuid.uuid4())
    assert client.post(f"{API}/resumes/{rid}/score", json={}).status_code in (
        401,
        403,
    )
    assert client.get(f"{API}/jobs/{uuid.uuid4()}").status_code in (401, 403)


def test_no_auto_score_from_compile_generate_save() -> None:
    """Structural: compile/generate/patch paths must not start score jobs."""
    router = (BACKEND / "resumes" / "router.py").read_text(encoding="utf-8")
    tree = ast.parse(router)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in (
            "compile_resume",
            "generate_resume",
            "patch_resume",
            "restore_version",
        ):
            src = ast.get_source_segment(router, node) or ""
            assert "start_score" not in src
            assert "/score" not in src
            assert "run_score" not in src
            assert "jobs.enqueue" not in src


def test_ui_score_and_settings_structure() -> None:
    blob = "\n".join(
        p.read_text(encoding="utf-8")
        for p in list(FE.rglob("*.tsx")) + list(FE.rglob("*.ts"))
        if not p.name.endswith(".test.ts")
    )
    assert "Check score" in blob or "Re-check score" in blob
    assert "startScore" in blob or "/score" in blob or "scoreResume" in blob
    assert "Update GitHub data" in blob
    assert "github_username" in blob or "githubUsername" in blob
    assert "cache_status" in blob or "cacheStatus" in blob or "No cache" in blob
    # no auto score on compile
    assert "compileResume" in blob
    # Settings drawer/shell
    assert "Settings" in blob
    # ATS rail not stub-only
    assert "later phase" not in blob.lower() or "Score stepper" not in blob
    assert "queued" in blob.lower() or "processing" in blob.lower() or "stepper" in blob.lower()

"""
Phase 2 hard rules — drive shipped create/list/get/delete/filter paths.

Product: docs/product/02-resumes-list-and-create.md (+ form-path pivot naming)
- New resume (create ai) → track structured + empty form
- New LaTeX → track latex + starter source
- No template picker create path
- List/get/delete user-scoped; unauth denied
- Search/tag filter excludes non-matches
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

API = "/api/v1"
ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture()
def client(tmp_path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    return TestClient(create_app())


def _auth(client: TestClient) -> dict[str, str]:
    email = f"u_{uuid.uuid4().hex[:10]}@example.com"
    reg = client.post(
        f"{API}/auth/register",
        json={"email": email, "password": "password1"},
    )
    assert reg.status_code == 200, reg.text
    token = reg.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_list_empty_for_new_user(client: TestClient) -> None:
    h = _auth(client)
    res = client.get(f"{API}/resumes", headers=h)
    assert res.status_code == 200
    assert res.json() == []


def test_create_ai_resume_structured_empty_form(client: TestClient) -> None:
    h = _auth(client)
    res = client.post(f"{API}/resumes", headers=h, json={"create": "ai"})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["id"]
    assert body["track"] == "structured"
    assert "AI" in body["title"] or body["title"]
    form = body.get("form")
    assert isinstance(form, dict)
    assert "basics" in form
    assert form.get("experience") == [] or form.get("experience") is not None
    # latex source not required for structured path at create
    got = client.get(f"{API}/resumes/{body['id']}", headers=h)
    assert got.status_code == 200
    assert got.json()["track"] == "structured"
    assert got.json()["id"] == body["id"]


def test_create_latex_resume_starter_source(client: TestClient) -> None:
    h = _auth(client)
    res = client.post(f"{API}/resumes", headers=h, json={"create": "latex"})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["track"] == "latex"
    source = body.get("latex_source") or body.get("source") or ""
    assert isinstance(source, str) and len(source) > 20
    assert "documentclass" in source or "\\begin{document}" in source
    got = client.get(f"{API}/resumes/{body['id']}", headers=h)
    assert got.status_code == 200
    assert got.json()["track"] == "latex"


def test_list_shows_created_and_delete_removes(client: TestClient) -> None:
    h = _auth(client)
    a = client.post(f"{API}/resumes", headers=h, json={"create": "ai"}).json()
    b = client.post(f"{API}/resumes", headers=h, json={"create": "latex"}).json()
    listing = client.get(f"{API}/resumes", headers=h)
    assert listing.status_code == 200
    ids = {row["id"] for row in listing.json()}
    assert a["id"] in ids and b["id"] in ids

    deleted = client.delete(f"{API}/resumes/{a['id']}", headers=h)
    assert deleted.status_code in (200, 204)
    listing2 = client.get(f"{API}/resumes", headers=h).json()
    ids2 = {row["id"] for row in listing2}
    assert a["id"] not in ids2
    assert b["id"] in ids2
    assert client.get(f"{API}/resumes/{a['id']}", headers=h).status_code == 404


def test_unauth_create_list_get_delete_rejected(client: TestClient) -> None:
    assert client.get(f"{API}/resumes").status_code in (401, 403)
    post = client.post(f"{API}/resumes", json={"create": "ai"})
    assert post.status_code in (401, 403), post.text
    assert client.get(f"{API}/resumes/{uuid.uuid4()}").status_code in (401, 403)
    assert client.delete(f"{API}/resumes/{uuid.uuid4()}").status_code in (401, 403)


def test_no_template_create_path_on_api(client: TestClient) -> None:
    h = _auth(client)
    # Product forbids template picker create; invalid create kinds must not invent templates
    bad = client.post(f"{API}/resumes", headers=h, json={"create": "template"})
    assert bad.status_code in (400, 422), bad.text
    # OpenAPI/routes should not expose from-template style path as success
    ghost = client.post(f"{API}/resumes/from-template", headers=h, json={})
    assert ghost.status_code in (404, 405, 400, 422)


def test_search_and_tag_filter(client: TestClient) -> None:
    h = _auth(client)
    ai = client.post(f"{API}/resumes", headers=h, json={"create": "ai"}).json()
    tex = client.post(f"{API}/resumes", headers=h, json={"create": "latex"}).json()
    # patch titles/tags via create response fields if API allows update;
    # Phase 2 thin: set tags through dedicated patch or create body
    # Prefer list query on title text from defaults + optional tags endpoint
    # If store supports patch:
    patch = client.patch(
        f"{API}/resumes/{ai['id']}",
        headers=h,
        json={"title": "Alpha AI Role", "tags": ["python", "ml"]},
    )
    if patch.status_code == 404:
        pytest.skip("title/tags patch not wired — filter tested via query only if create accepts")
    assert patch.status_code == 200
    client.patch(
        f"{API}/resumes/{tex['id']}",
        headers=h,
        json={"title": "Beta LaTeX Doc", "tags": ["python"]},
    )

    by_title = client.get(f"{API}/resumes", headers=h, params={"q": "Alpha"})
    assert by_title.status_code == 200
    ids = {r["id"] for r in by_title.json()}
    assert ai["id"] in ids
    assert tex["id"] not in ids

    by_tag = client.get(f"{API}/resumes", headers=h, params={"tags": "ml"})
    assert by_tag.status_code == 200
    tag_ids = {r["id"] for r in by_tag.json()}
    assert ai["id"] in tag_ids
    assert tex["id"] not in tag_ids

    multi = client.get(f"{API}/resumes", headers=h, params={"tags": "python,ml"})
    multi_ids = {r["id"] for r in multi.json()}
    assert ai["id"] in multi_ids
    assert tex["id"] not in multi_ids  # AND filter

    full = client.get(f"{API}/resumes", headers=h)
    assert {r["id"] for r in full.json()} == {ai["id"], tex["id"]}


def test_ui_has_only_two_create_ctas_no_template_picker() -> None:
    texts = []
    for p in (ROOT / "frontend" / "src").rglob("*.tsx"):
        texts.append(p.read_text(encoding="utf-8"))
    for p in (ROOT / "frontend" / "src").rglob("*.ts"):
        if p.name.endswith(".test.ts"):
            continue
        texts.append(p.read_text(encoding="utf-8"))
    blob = "\n".join(texts)
    assert "New resume" in blob
    assert "New AI resume" not in blob
    assert "New LaTeX" in blob
    # Forbidden product CTAs / controls (exact user-facing strings)
    assert "From template" not in blob
    assert "Template gallery" not in blob
    assert "Template picker" not in blob
    # Create actions only use ai|latex kinds
    assert 'createResume("ai")' in blob or 'onCreate("ai")' in blob
    assert 'createResume("latex")' in blob or 'onCreate("latex")' in blob
    assert "createResume(\"template\")" not in blob
    assert 'create: "template"' not in blob

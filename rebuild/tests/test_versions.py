"""
Phase 6 hard rules — LaTeX version checkpoints.

Product: docs/product/07-versions.md
- commit / list / restore / delete (auth required)
- unchanged commit is a no-op (no new row)
- restore replaces live latex only (not form JSON)
- empty list surfaces product empty-state copy in UI
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.resumes.versions import DEFAULT_MESSAGE, latex_unchanged, normalize_message

API = "/api/v1"
ROOT = Path(__file__).resolve().parent.parent
FE = ROOT / "frontend" / "src"

TEX_A = r"""\documentclass{article}
\begin{document}
Version A
\end{document}
"""

TEX_B = r"""\documentclass{article}
\begin{document}
Version B changed
\end{document}
"""


@pytest.fixture()
def client(tmp_path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    return TestClient(create_app())


def _auth(client: TestClient) -> dict[str, str]:
    email = f"v_{uuid.uuid4().hex[:10]}@example.com"
    reg = client.post(
        f"{API}/auth/register",
        json={"email": email, "password": "password1"},
    )
    assert reg.status_code == 200, reg.text
    return {"Authorization": f"Bearer {reg.json()['access_token']}"}


def _latex_resume(
    client: TestClient, h: dict[str, str], source: str = TEX_A
) -> str:
    r = client.post(f"{API}/resumes", headers=h, json={"create": "latex"})
    assert r.status_code == 200
    rid = r.json()["id"]
    p = client.patch(
        f"{API}/resumes/{rid}",
        headers=h,
        json={"latex_source": source, "title": "Versions Me"},
    )
    assert p.status_code == 200
    return rid


def test_pure_unchanged_compare() -> None:
    assert latex_unchanged("same", "same") is True
    assert latex_unchanged("a", "b") is False
    assert latex_unchanged(None, None) is True
    assert latex_unchanged("", None) is True
    assert latex_unchanged("x", None) is False


def test_normalize_message_default_and_max() -> None:
    assert normalize_message(None) == DEFAULT_MESSAGE
    assert normalize_message("") == DEFAULT_MESSAGE
    assert normalize_message("  hi  ") == "hi"
    long = "x" * 250
    assert len(normalize_message(long)) == 200


def test_versions_unauth_denied(client: TestClient) -> None:
    rid = "00000000-0000-0000-0000-000000000001"
    assert client.get(f"{API}/resumes/{rid}/versions").status_code in (401, 403)
    assert client.post(f"{API}/resumes/{rid}/versions", json={}).status_code in (
        401,
        403,
    )


def test_commit_list_unchanged_restore_delete(client: TestClient) -> None:
    h = _auth(client)
    rid = _latex_resume(client, h, TEX_A)

    empty = client.get(f"{API}/resumes/{rid}/versions", headers=h)
    assert empty.status_code == 200
    assert empty.json() == []

    c1 = client.post(
        f"{API}/resumes/{rid}/versions",
        headers=h,
        json={"message": "first snap"},
    )
    assert c1.status_code == 200, c1.text
    body1 = c1.json()
    assert body1["committed"] is True
    assert body1.get("unchanged") is not True
    assert body1["checkpoint"]["message"] == "first snap"
    assert body1["checkpoint"]["latex_source"] == TEX_A
    cp1_id = body1["checkpoint"]["id"]

    listed = client.get(f"{API}/resumes/{rid}/versions", headers=h)
    assert listed.status_code == 200
    rows = listed.json()
    assert len(rows) == 1
    assert rows[0]["id"] == cp1_id
    assert rows[0]["message"] == "first snap"
    assert "created_at" in rows[0]
    # list may omit full latex for scannability, or include it
    assert "id" in rows[0]

    # unchanged: same live source → no new row
    c2 = client.post(
        f"{API}/resumes/{rid}/versions",
        headers=h,
        json={"message": "again"},
    )
    assert c2.status_code == 200, c2.text
    body2 = c2.json()
    assert body2["committed"] is False
    assert body2["unchanged"] is True
    assert "no changes" in (body2.get("detail") or body2.get("message") or "").lower()
    listed2 = client.get(f"{API}/resumes/{rid}/versions", headers=h).json()
    assert len(listed2) == 1

    # real change → second checkpoint
    patch = client.patch(
        f"{API}/resumes/{rid}",
        headers=h,
        json={"latex_source": TEX_B},
    )
    assert patch.status_code == 200
    c3 = client.post(
        f"{API}/resumes/{rid}/versions",
        headers=h,
        json={"message": "second"},
    )
    assert c3.status_code == 200
    assert c3.json()["committed"] is True
    rows3 = client.get(f"{API}/resumes/{rid}/versions", headers=h).json()
    assert len(rows3) == 2
    # newest first
    assert rows3[0]["message"] == "second"
    assert rows3[1]["message"] == "first snap"

    # restore older (first snap) → live latex is TEX_A; form not rewritten
    form_before = client.get(f"{API}/resumes/{rid}", headers=h).json().get("form")
    rest = client.post(
        f"{API}/resumes/{rid}/versions/{cp1_id}/restore",
        headers=h,
    )
    assert rest.status_code == 200, rest.text
    restored = rest.json()
    # response is resume detail (or wraps it)
    latex = restored.get("latex_source") or restored.get("resume", {}).get(
        "latex_source"
    )
    assert latex == TEX_A
    got = client.get(f"{API}/resumes/{rid}", headers=h).json()
    assert got["latex_source"] == TEX_A
    assert got.get("form") == form_before
    # track stays latex-centric (still latex for this resume)
    assert got["track"] == "latex"

    # delete one checkpoint; resume remains
    d = client.delete(f"{API}/resumes/{rid}/versions/{cp1_id}", headers=h)
    assert d.status_code in (200, 204), d.text
    rows_after = client.get(f"{API}/resumes/{rid}/versions", headers=h).json()
    assert len(rows_after) == 1
    assert rows_after[0]["message"] == "second"
    still = client.get(f"{API}/resumes/{rid}", headers=h)
    assert still.status_code == 200
    assert still.json()["id"] == rid


def test_commit_default_message(client: TestClient) -> None:
    h = _auth(client)
    rid = _latex_resume(client, h, TEX_A)
    c = client.post(f"{API}/resumes/{rid}/versions", headers=h, json={})
    assert c.status_code == 200
    assert c.json()["committed"] is True
    assert c.json()["checkpoint"]["message"] == DEFAULT_MESSAGE


def test_versions_scoped_to_owner(client: TestClient) -> None:
    h1 = _auth(client)
    h2 = _auth(client)
    rid = _latex_resume(client, h1, TEX_A)
    client.post(
        f"{API}/resumes/{rid}/versions",
        headers=h1,
        json={"message": "mine"},
    )
    assert client.get(f"{API}/resumes/{rid}/versions", headers=h2).status_code == 404
    assert (
        client.post(
            f"{API}/resumes/{rid}/versions", headers=h2, json={}
        ).status_code
        == 404
    )


def test_frontend_versions_rail_structure() -> None:
    """Structural UI: Versions rail has Commit, empty state, restore/delete confirms."""
    ws = (FE / "Workspace.tsx").read_text(encoding="utf-8")
    api = (FE / "api.ts").read_text(encoding="utf-8")
    assert "No checkpoints yet" in ws
    assert "Commit" in ws
    assert "Restore" in ws
    assert "Delete" in ws
    assert "confirm" in ws.lower()
    assert "No changes since last commit" in ws or "unchanged" in ws.lower()
    assert "listVersions" in api or "commitVersion" in api
    assert "restoreVersion" in api or "/versions/" in api
    # stub copy must be gone
    assert "later phase" not in ws.lower() or "Score job" in ws  # score may still stub
    assert "Commit / restore in a later phase" not in ws

"""
Phase 3 hard rules — workspace mode chrome + save/reload.

Form-path pivot:
- structured → FORM_PATH: form only; no Source; no AI Generate; no Lint
- latex → LATEX_ONLY: source + Lint; no Form; no AI Generate
- Save persists title, tags, form and/or latex_source
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.resumes.mode import workspace_mode_for_track

API = "/api/v1"
ROOT = Path(__file__).resolve().parent.parent
FE = ROOT / "frontend" / "src"


@pytest.fixture()
def client(tmp_path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    return TestClient(create_app())


def _auth(client: TestClient) -> dict[str, str]:
    email = f"w_{uuid.uuid4().hex[:10]}@example.com"
    reg = client.post(
        f"{API}/auth/register",
        json={"email": email, "password": "password1"},
    )
    assert reg.status_code == 200, reg.text
    return {"Authorization": f"Bearer {reg.json()['access_token']}"}


def test_mode_helper_maps_tracks() -> None:
    assert workspace_mode_for_track("structured")["mode"] == "FORM_PATH"
    assert workspace_mode_for_track("structured")["show_form_tab"] is True
    assert workspace_mode_for_track("structured")["show_source_editor"] is False
    assert workspace_mode_for_track("structured")["show_lint"] is False
    assert workspace_mode_for_track("latex")["mode"] == "LATEX_ONLY"
    assert workspace_mode_for_track("latex")["show_form_tab"] is False
    assert workspace_mode_for_track("latex")["show_source_editor"] is True
    assert workspace_mode_for_track("latex")["show_lint"] is True


def test_get_includes_mode_flags(client: TestClient) -> None:
    h = _auth(client)
    ai = client.post(f"{API}/resumes", headers=h, json={"create": "ai"}).json()
    lx = client.post(f"{API}/resumes", headers=h, json={"create": "latex"}).json()
    g_ai = client.get(f"{API}/resumes/{ai['id']}", headers=h).json()
    g_lx = client.get(f"{API}/resumes/{lx['id']}", headers=h).json()
    assert g_ai["mode"] == "FORM_PATH"
    assert g_ai["show_form_tab"] is True
    assert g_ai["show_source_editor"] is False
    assert g_ai["show_lint"] is False
    assert g_lx["mode"] == "LATEX_ONLY"
    assert g_lx["show_form_tab"] is False
    assert g_lx["show_source_editor"] is True
    assert g_lx["show_lint"] is True


def test_save_structured_form_title_tags_reload(client: TestClient) -> None:
    h = _auth(client)
    ai = client.post(f"{API}/resumes", headers=h, json={"create": "ai"}).json()
    form = {
        "basics": {
            "name": "Ada Lovelace",
            "email": "ada@example.com",
            "phone": "555",
            "location": "London",
            "summary": "Math",
            "links": [{"label": "GitHub", "url": "https://github.com/ada"}],
        },
        "experience": [
            {
                "company": "Analytical Engines",
                "position": "Engineer",
                "dates": "1840-1843",
                "summary": "Programs",
            }
        ],
        "education": [
            {"institution": "Home", "area": "Math", "degree": "—", "dates": "1830"}
        ],
        "projects": [
            {
                "name": "Notes",
                "description": "On Babbage",
                "url": "",
                "highlights": ["First algorithm"],
            }
        ],
        "skills": [{"name": "Languages", "keywords": "math, logic"}],
    }
    res = client.patch(
        f"{API}/resumes/{ai['id']}",
        headers=h,
        json={
            "title": "Ada CV",
            "tags": ["math", "history"],
            "form": form,
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["title"] == "Ada CV"
    assert body["tags"] == ["math", "history"]
    assert body["form"]["basics"]["name"] == "Ada Lovelace"
    assert body["form"]["experience"][0]["company"] == "Analytical Engines"

    got = client.get(f"{API}/resumes/{ai['id']}", headers=h).json()
    assert got["title"] == "Ada CV"
    assert got["form"]["basics"]["email"] == "ada@example.com"
    assert got["form"]["skills"][0]["keywords"] == "math, logic"
    assert got["track"] == "structured"
    assert got["mode"] == "FORM_PATH"


def test_save_latex_source_reload(client: TestClient) -> None:
    h = _auth(client)
    lx = client.post(f"{API}/resumes", headers=h, json={"create": "latex"}).json()
    source = "\\documentclass{article}\\begin{document}Hello Phase3\\end{document}"
    res = client.patch(
        f"{API}/resumes/{lx['id']}",
        headers=h,
        json={"title": "Latex Edit", "tags": ["tex"], "latex_source": source},
    )
    assert res.status_code == 200, res.text
    got = client.get(f"{API}/resumes/{lx['id']}", headers=h).json()
    assert got["title"] == "Latex Edit"
    assert "Hello Phase3" in (got.get("latex_source") or "")
    assert got["mode"] == "LATEX_ONLY"
    assert got["show_form_tab"] is False


def test_unauth_patch_denied(client: TestClient) -> None:
    assert client.patch(
        f"{API}/resumes/{uuid.uuid4()}",
        json={"title": "x"},
    ).status_code in (401, 403)


def test_ui_workspace_mode_chrome_structure() -> None:
    texts = []
    for p in FE.rglob("*.tsx"):
        texts.append(p.read_text(encoding="utf-8"))
    for p in FE.rglob("*.ts"):
        if p.name.endswith(".test.ts"):
            continue
        texts.append(p.read_text(encoding="utf-8"))
    blob = "\n".join(texts)

    # Two-tier chrome labels
    assert "File" in blob and "Build" in blob and "Score" in blob and "Danger" in blob
    assert "Save" in blob
    assert "Compile" in blob
    assert "AI Generate" not in blob

    # Mode helper used for chrome
    assert "FORM_PATH" in blob or "showFormTab" in blob
    assert "LATEX_ONLY" in blob or "showSourceEditor" in blob
    assert "showLint" in blob

    # Layout regions
    assert "rail" in blob.lower() or "Versions" in blob
    assert "editor" in blob.lower() or "Form" in blob
    assert "PDF" in blob or "pdf" in blob

    # Contact on form
    assert "LinkedIn" in blob or "linkedin" in blob.lower() or "GitHub" in blob

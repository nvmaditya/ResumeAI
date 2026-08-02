"""
Form→LaTeX helpers + legacy generate endpoint (no track flip).

Product pivot: Compile owns form→PDF; /generate must not flip to LATEX_ONLY.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.generate.form_to_latex import form_to_latex
from app.generate.service import generate_from_form
from app.main import create_app

API = "/api/v1"

SAMPLE_FORM = {
    "basics": {
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "phone": "555",
        "location": "London",
        "summary": "Mathematician",
        "linkedin": "linkedin.com/in/ada",
        "github": "ada",
        "website": "",
        "links": [],
    },
    "experience": [
        {
            "company": "Analytical Engines",
            "position": "Engineer",
            "dates": "1840-1843",
            "summary": "Wrote notes\nOn Babbage",
        }
    ],
    "education": [
        {"institution": "Home", "area": "Math", "degree": "—", "dates": "1830"}
    ],
    "projects": [
        {
            "name": "Notes",
            "description": "On the engine",
            "url": "",
            "highlights": ["First algorithm"],
        }
    ],
    "skills": [{"name": "Languages", "keywords": "math, logic"}],
}


@pytest.fixture()
def client(tmp_path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    return TestClient(create_app())


def _auth(client: TestClient) -> dict[str, str]:
    email = f"g_{uuid.uuid4().hex[:10]}@example.com"
    reg = client.post(
        f"{API}/auth/register",
        json={"email": email, "password": "password1"},
    )
    assert reg.status_code == 200, reg.text
    return {"Authorization": f"Bearer {reg.json()['access_token']}"}


def test_form_to_latex_emits_full_document() -> None:
    tex = form_to_latex(SAMPLE_FORM, title="Ada")
    assert r"\documentclass" in tex
    assert r"\begin{document}" in tex
    assert r"\end{document}" in tex
    assert "Ada Lovelace" in tex
    assert "Analytical Engines" in tex
    assert "ada@example.com" in tex
    assert "colorlinks=true" in tex
    assert "urlcolor=blue" in tex
    assert "pdfborder={0 0 0}" in tex


def test_form_to_latex_honors_section_order() -> None:
    data = {
        **SAMPLE_FORM,
        "section_order": ["skills", "experience", "education", "projects"],
    }
    tex = form_to_latex(data, title="Ada")
    i_skills = tex.index("Skills")
    i_exp = tex.index("Experience")
    assert i_skills < i_exp


def test_generate_service_fallback_used_llm_false_and_repair() -> None:
    result = generate_from_form(SAMPLE_FORM, title="Ada", use_llm=False)
    assert result.used_llm is False
    assert result.latex
    assert r"\begin{document}" in result.latex
    assert result.iterations >= 1


def test_generate_structured_stays_form_path_returns_used_llm(
    client: TestClient,
) -> None:
    """Legacy /generate: latex snapshot + used_llm; does NOT flip track."""
    h = _auth(client)
    created = client.post(f"{API}/resumes", headers=h, json={"create": "ai"}).json()
    assert created["track"] == "structured"
    client.patch(
        f"{API}/resumes/{created['id']}",
        headers=h,
        json={"form": SAMPLE_FORM, "title": "Ada CV"},
    )
    res = client.post(f"{API}/resumes/{created['id']}/generate", headers=h)
    assert res.status_code == 200, res.text
    body = res.json()
    assert "used_llm" in body
    assert isinstance(body["used_llm"], bool)
    assert body["track"] == "structured"
    assert body.get("mode") == "FORM_PATH"
    assert body.get("show_form_tab") is True
    src = body.get("latex_source") or body.get("latex")
    assert src and len(src) > 50

    got = client.get(f"{API}/resumes/{created['id']}", headers=h).json()
    assert got["track"] == "structured"
    assert got["show_form_tab"] is True
    assert got["show_source_editor"] is False
    assert (got.get("latex_source") or "").strip()


def test_generate_rejects_latex_track(client: TestClient) -> None:
    h = _auth(client)
    lx = client.post(f"{API}/resumes", headers=h, json={"create": "latex"}).json()
    res = client.post(f"{API}/resumes/{lx['id']}/generate", headers=h)
    assert res.status_code in (400, 409, 422)
    still = client.get(f"{API}/resumes/{lx['id']}", headers=h).json()
    assert still["track"] == "latex"


def test_generate_unauth_denied(client: TestClient) -> None:
    assert client.post(f"{API}/resumes/{uuid.uuid4()}/generate").status_code in (
        401,
        403,
    )


def test_generate_failed_does_not_flip_track(client: TestClient, monkeypatch) -> None:
    h = _auth(client)
    created = client.post(f"{API}/resumes", headers=h, json={"create": "ai"}).json()

    def boom(*_a, **_k):
        raise RuntimeError("forced generate failure")

    monkeypatch.setattr(
        "app.resumes.router.generate_from_form",
        boom,
    )
    res = client.post(f"{API}/resumes/{created['id']}/generate", headers=h)
    assert res.status_code in (400, 500)
    got = client.get(f"{API}/resumes/{created['id']}", headers=h).json()
    assert got["track"] == "structured"
    assert got["show_form_tab"] is True


def test_ui_no_ai_generate_compile_owns_form_path() -> None:
    from pathlib import Path

    fe = Path(__file__).resolve().parent.parent / "frontend" / "src"
    blob = "\n".join(
        p.read_text(encoding="utf-8")
        for p in list(fe.rglob("*.tsx")) + list(fe.rglob("*.ts"))
        if not p.name.endswith(".test.ts")
    )
    assert "AI Generate" not in blob
    assert "compileResume" in blob
    assert "New resume" in blob

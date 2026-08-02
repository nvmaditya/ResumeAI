"""
Form-path product pivot (grilling shared understanding).

- New resume (not "New AI"); no AI Generate chrome
- FORM_PATH: form only, no Source tab, Lint hidden, track stays structured
- Compile on structured: deterministic form→LaTeX + PDF; form still editable
- .tex = last successful compile snapshot
- LATEX_ONLY: source + lint with suggestions; existing latex stays latex
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.compile.lint import lint_latex
from app.main import create_app
from app.resumes.mode import workspace_mode_for_track

API = "/api/v1"
ROOT = Path(__file__).resolve().parent.parent
FE = ROOT / "frontend" / "src"

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
            "summary": "Wrote notes",
        }
    ],
    "education": [
        {"institution": "Home", "area": "Math", "degree": "—", "dates": "1830"}
    ],
    "projects": [],
    "skills": [{"name": "Languages", "keywords": "math, logic"}],
}


@pytest.fixture()
def client(tmp_path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    return TestClient(create_app())


def _auth(client: TestClient) -> dict[str, str]:
    email = f"fp_{uuid.uuid4().hex[:10]}@example.com"
    reg = client.post(
        f"{API}/auth/register",
        json={"email": email, "password": "password1"},
    )
    assert reg.status_code == 200, reg.text
    return {"Authorization": f"Bearer {reg.json()['access_token']}"}


def test_mode_form_path_no_source_no_lint() -> None:
    m = workspace_mode_for_track("structured")
    assert m["mode"] == "FORM_PATH"
    assert m["show_form_tab"] is True
    assert m["show_source_editor"] is False
    assert m["show_lint"] is False


def test_mode_latex_source_and_lint() -> None:
    m = workspace_mode_for_track("latex")
    assert m["mode"] == "LATEX_ONLY"
    assert m["show_form_tab"] is False
    assert m["show_source_editor"] is True
    assert m["show_lint"] is True


def test_compile_structured_stays_form_path_writes_latex_and_pdf(
    client: TestClient,
) -> None:
    h = _auth(client)
    created = client.post(f"{API}/resumes", headers=h, json={"create": "ai"}).json()
    rid = created["id"]
    assert created["track"] == "structured"
    client.patch(
        f"{API}/resumes/{rid}",
        headers=h,
        json={"form": SAMPLE_FORM, "title": "Ada CV"},
    )
    res = client.post(f"{API}/resumes/{rid}/compile", headers=h)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["ok"] is True
    assert body["engine"] in ("tectonic", "layout")
    assert body["size"] >= 200

    got = client.get(f"{API}/resumes/{rid}", headers=h).json()
    assert got["track"] == "structured"
    assert got["mode"] == "FORM_PATH"
    assert got["show_form_tab"] is True
    assert got["show_source_editor"] is False
    assert got["show_lint"] is False
    # form still present / editable SoT
    assert got["form"]["basics"]["name"] == "Ada Lovelace"
    src = (got.get("latex_source") or "").strip()
    assert len(src) > 50
    assert r"\documentclass" in src
    assert "Ada Lovelace" in src

    pdf = client.get(f"{API}/resumes/{rid}/pdf", headers=h)
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF")

    tex = client.get(f"{API}/resumes/{rid}/tex", headers=h)
    assert tex.status_code == 200
    assert b"documentclass" in tex.content or b"Ada" in tex.content


def test_compile_does_not_flip_existing_latex(client: TestClient) -> None:
    h = _auth(client)
    lx = client.post(f"{API}/resumes", headers=h, json={"create": "latex"}).json()
    assert lx["track"] == "latex"
    res = client.post(f"{API}/resumes/{lx['id']}/compile", headers=h)
    assert res.status_code == 200
    got = client.get(f"{API}/resumes/{lx['id']}", headers=h).json()
    assert got["track"] == "latex"
    assert got["mode"] == "LATEX_ONLY"
    assert got["show_source_editor"] is True
    assert got["show_lint"] is True


def test_latex_lint_includes_fix_suggestions() -> None:
    broken = r"""\documentclass{article}
\begin{document}
\begin{itemize}
\item one
\end{document}
"""
    diags = lint_latex(broken, track="latex")
    assert len(diags) >= 1
    msgs = " ".join(d["message"].lower() for d in diags)
    # env imbalance + a short fix hint
    assert "itemize" in msgs or "end" in msgs
    assert any(
        d.get("suggestion") or "add" in d["message"].lower() or "fix" in d["message"].lower()
        or "\\end" in d["message"]
        for d in diags
    )


def test_ui_new_resume_no_ai_branding_form_path_chrome() -> None:
    blob = "\n".join(
        p.read_text(encoding="utf-8")
        for p in list(FE.rglob("*.tsx")) + list(FE.rglob("*.ts"))
        if not p.name.endswith(".test.ts")
    )
    assert "New resume" in blob
    assert "New AI resume" not in blob
    assert "AI Generate" not in blob
    # form path: lint gated; latex path still has Lint control string somewhere
    assert "showLint" in blob or "show_lint" in blob
    assert "showSourceEditor" in blob or "show_source_editor" in blob
    assert "New LaTeX" in blob
    # Diagnostics only when showLint (no form-path stub copy)
    assert "Lint is for LaTeX resumes" not in blob
    # sections/entries reorderable without DnD (↑/↓)
    assert "section_order" in blob
    assert "moveSection" in blob or "reorderList" in blob or "↑" in blob
    assert "DND_" not in blob
    assert "drag-handle" not in blob
    # plain soft-wrap editor (no dual-layer highlight)
    assert "source-editor" in blob
    assert "wrap=\"soft\"" in blob or "wrap='soft'" in blob
    assert "latexHighlight" not in blob
    assert "source-highlight" not in blob
    # no primary generate CTA
    assert "generateResume" not in blob
    assert "AI Generate" not in blob

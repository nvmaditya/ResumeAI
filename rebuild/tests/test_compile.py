"""
Phase 4 hard rules — compile / lint / downloads.

Product: docs/product/08-compile-pdf-lint-downloads.md
- success PDF starts with %PDF
- failure does not return fake PDF body
- tectonic preferred, layout fallback OK
- lint returns structured diagnostics
- unauth denied
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.compile.engine import build_compiler
from app.compile.layout import render_layout_pdf
from app.main import create_app

API = "/api/v1"

MIN_TEX = r"""\documentclass{article}
\begin{document}
Hello Phase Four
\end{document}
"""


@pytest.fixture()
def client(tmp_path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    return TestClient(create_app())


def _auth(client: TestClient) -> dict[str, str]:
    email = f"c_{uuid.uuid4().hex[:10]}@example.com"
    reg = client.post(
        f"{API}/auth/register",
        json={"email": email, "password": "password1"},
    )
    assert reg.status_code == 200, reg.text
    return {"Authorization": f"Bearer {reg.json()['access_token']}"}


def _latex_resume(client: TestClient, h: dict[str, str], source: str = MIN_TEX) -> str:
    r = client.post(f"{API}/resumes", headers=h, json={"create": "latex"})
    assert r.status_code == 200
    rid = r.json()["id"]
    p = client.patch(
        f"{API}/resumes/{rid}",
        headers=h,
        json={"latex_source": source, "title": "Compile Me"},
    )
    assert p.status_code == 200
    return rid


def test_layout_pdf_header_is_valid() -> None:
    pdf = render_layout_pdf(title="T", latex=MIN_TEX)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 200
    assert b"%%EOF" in pdf[-32:] or b"EOF" in pdf[-64:]


def test_compiler_service_returns_pdf() -> None:
    c = build_compiler(None)
    result = c.compile_tex(MIN_TEX, title="Resume")
    assert result.ok
    assert result.pdf.startswith(b"%PDF")
    assert result.engine in ("tectonic", "layout")
    assert result.size == len(result.pdf)


def test_compile_endpoint_returns_pdf_header(client: TestClient) -> None:
    h = _auth(client)
    rid = _latex_resume(client, h)
    res = client.post(f"{API}/resumes/{rid}/compile", headers=h)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body.get("ok") is True
    assert body.get("engine") in ("tectonic", "layout")
    assert int(body.get("size") or 0) > 200
    # PDF bytes via dedicated download
    pdf = client.get(f"{API}/resumes/{rid}/pdf", headers=h)
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF")
    assert "pdf" in (pdf.headers.get("content-type") or "").lower()


def test_compile_empty_source_fails_without_fake_pdf(client: TestClient) -> None:
    h = _auth(client)
    rid = _latex_resume(client, h, source="   ")
    res = client.post(f"{API}/resumes/{rid}/compile", headers=h)
    assert res.status_code in (400, 422)
    # Must not return a 200 PDF download of garbage after failed compile
    pdf = client.get(f"{API}/resumes/{rid}/pdf", headers=h)
    assert pdf.status_code in (404, 400, 409)


def test_tex_download(client: TestClient) -> None:
    h = _auth(client)
    rid = _latex_resume(client, h)
    res = client.get(f"{API}/resumes/{rid}/tex", headers=h)
    assert res.status_code == 200
    assert b"documentclass" in res.content or b"begin{document}" in res.content
    cd = res.headers.get("content-disposition") or ""
    assert ".tex" in cd or "tex" in (res.headers.get("content-type") or "")


def test_lint_clean_and_issues(client: TestClient) -> None:
    h = _auth(client)
    rid = _latex_resume(client, h, source=MIN_TEX)
    clean = client.post(f"{API}/resumes/{rid}/lint", headers=h)
    assert clean.status_code == 200
    body = clean.json()
    assert "diagnostics" in body
    assert isinstance(body["diagnostics"], list)

    broken = client.patch(
        f"{API}/resumes/{rid}",
        headers=h,
        json={"latex_source": "\\documentclass{article}\n\\begin{document}\n"},
    )
    assert broken.status_code == 200
    dirty = client.post(f"{API}/resumes/{rid}/lint", headers=h)
    assert dirty.status_code == 200
    diags = dirty.json()["diagnostics"]
    assert isinstance(diags, list)
    assert len(diags) >= 1
    d0 = diags[0]
    assert "message" in d0
    assert "severity" in d0
    # line optional but preferred
    assert "line" in d0


def test_lint_structured_form_resume_empty_source_is_clean(client: TestClient) -> None:
    """FORM_PATH / New resume: empty latex until Compile — not a lint error."""
    h = _auth(client)
    ai = client.post(f"{API}/resumes", headers=h, json={"create": "ai"})
    assert ai.status_code == 200
    body = ai.json()
    assert body["track"] == "structured"
    assert not (body.get("latex_source") or "").strip()
    lint = client.post(f"{API}/resumes/{body['id']}/lint", headers=h)
    assert lint.status_code == 200, lint.text
    data = lint.json()
    assert data["diagnostics"] == []
    assert data["count"] == 0
    # latex track with empty source still errors (+ fix suggestion)
    lx = client.post(f"{API}/resumes", headers=h, json={"create": "latex"}).json()
    client.patch(
        f"{API}/resumes/{lx['id']}",
        headers=h,
        json={"latex_source": "   "},
    )
    empty_lx = client.post(f"{API}/resumes/{lx['id']}/lint", headers=h)
    assert empty_lx.status_code == 200
    assert empty_lx.json()["count"] >= 1
    d0 = empty_lx.json()["diagnostics"][0]
    assert "message" in d0


def test_unauth_compile_denied(client: TestClient) -> None:
    assert client.post(f"{API}/resumes/{uuid.uuid4()}/compile").status_code in (
        401,
        403,
    )


def test_placeholder_images_for_missing_includegraphics() -> None:
    from app.compile.assets import ensure_placeholder_images, referenced_image_names

    tex = r"""\documentclass{article}
\usepackage{graphicx}
\begin{document}
\includegraphics[width=2cm]{profile.jpg}
\includegraphics{./photos/head.png}
\end{document}
"""
    assert "profile.jpg" in referenced_image_names(tex)
    assert "head.png" in referenced_image_names(tex)
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        created = ensure_placeholder_images(tex, Path(tmp))
        assert "profile.jpg" in created
        assert "head.png" in created
        assert (Path(tmp) / "profile.jpg").is_file()
        assert (Path(tmp) / "profile.jpg").stat().st_size > 20


def test_compile_with_missing_profile_jpg_does_not_hard_fail_on_asset(
    client: TestClient,
) -> None:
    """If tectonic is available, missing profile.jpg gets a placeholder and can compile."""
    from app.compile.engine import resolve_tectonic

    if resolve_tectonic(None) is None:
        pytest.skip("tectonic not installed")
    h = _auth(client)
    tex = r"""\documentclass{article}
\usepackage{graphicx}
\begin{document}
Hello
\includegraphics[width=1cm]{profile.jpg}
\end{document}
"""
    rid = _latex_resume(client, h, tex)
    res = client.post(f"{API}/resumes/{rid}/compile", headers=h)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["ok"] is True
    assert body["engine"] == "tectonic"
    pdf = client.get(f"{API}/resumes/{rid}/pdf", headers=h)
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF")
    assert client.get(f"{API}/resumes/{uuid.uuid4()}/pdf").status_code in (401, 403)


def test_health_reports_latex_engine(client: TestClient) -> None:
    res = client.get(f"{API}/health")
    assert res.status_code == 200
    body = res.json()
    assert body.get("latex_engine") in ("tectonic", "layout")

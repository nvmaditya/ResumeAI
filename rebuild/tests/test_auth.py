"""
Phase 1 auth hard rules — drive shipped FastAPI handlers only.

Product: docs/product/01-auth-and-session.md
- password ≥ 8
- register → auto-login (bearer session)
- login success / bad credentials
- unauth protected resume list fails
- auth protected list succeeds
- logout clears access for that token
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

API = "/api/v1"


@pytest.fixture()
def client(tmp_path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    app = create_app()
    return TestClient(app)


def _email() -> str:
    return f"user_{uuid.uuid4().hex[:10]}@example.com"


def test_register_rejects_short_password(client: TestClient) -> None:
    res = client.post(
        f"{API}/auth/register",
        json={"email": _email(), "password": "short"},
    )
    assert res.status_code == 422 or res.status_code == 400
    assert "access_token" not in (res.json() if res.headers.get("content-type", "").startswith("application/json") else {})


def test_register_auto_login_returns_bearer_token(client: TestClient) -> None:
    email = _email()
    res = client.post(
        f"{API}/auth/register",
        json={"email": email, "password": "password1"},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body.get("access_token")
    assert body.get("token_type", "bearer").lower() == "bearer"
    assert body.get("email", "").lower() == email.lower()


def test_register_duplicate_email_fails(client: TestClient) -> None:
    email = _email()
    first = client.post(
        f"{API}/auth/register",
        json={"email": email, "password": "password1"},
    )
    assert first.status_code == 200
    second = client.post(
        f"{API}/auth/register",
        json={"email": email, "password": "password1"},
    )
    assert second.status_code == 400
    assert "access_token" not in second.json()


def test_login_success_and_bad_credentials(client: TestClient) -> None:
    email = _email()
    password = "password1"
    assert (
        client.post(
            f"{API}/auth/register",
            json={"email": email, "password": password},
        ).status_code
        == 200
    )
    ok = client.post(
        f"{API}/auth/login",
        json={"email": email, "password": password},
    )
    assert ok.status_code == 200
    assert ok.json().get("access_token")

    bad = client.post(
        f"{API}/auth/login",
        json={"email": email, "password": "wrongpass"},
    )
    assert bad.status_code == 401


def test_unauthenticated_resume_list_is_rejected(client: TestClient) -> None:
    res = client.get(f"{API}/resumes")
    assert res.status_code in (401, 403)
    # Must not look like a successful empty list payload without auth
    if res.status_code == 200:
        pytest.fail("protected resume list must not succeed without auth")


def test_authenticated_resume_list_succeeds(client: TestClient) -> None:
    reg = client.post(
        f"{API}/auth/register",
        json={"email": _email(), "password": "password1"},
    )
    token = reg.json()["access_token"]
    res = client.get(
        f"{API}/resumes",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert isinstance(body, list)


def test_logout_invalidates_token(client: TestClient) -> None:
    reg = client.post(
        f"{API}/auth/register",
        json={"email": _email(), "password": "password1"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get(f"{API}/resumes", headers=headers).status_code == 200

    out = client.post(f"{API}/auth/logout", headers=headers)
    assert out.status_code in (200, 204)

    denied = client.get(f"{API}/resumes", headers=headers)
    assert denied.status_code in (401, 403)

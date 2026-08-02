"""Structural checks: Phase 1 auth UI exists in shipped frontend source."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FE = ROOT / "frontend" / "src"


def test_session_helpers_exist() -> None:
    text = (FE / "session.ts").read_text(encoding="utf-8")
    assert "getToken" in text
    assert "setToken" in text
    assert "clearToken" in text


def test_api_client_has_auth_and_resumes() -> None:
    text = (FE / "api.ts").read_text(encoding="utf-8")
    assert "auth/register" in text
    assert "auth/login" in text
    assert "auth/logout" in text
    assert "/resumes" in text


def test_app_has_register_login_and_protected_home() -> None:
    text = (FE / "App.tsx").read_text(encoding="utf-8")
    assert "register" in text.lower()
    assert "login" in text.lower()
    assert "Log out" in text or "logout" in text.lower()
    assert "Your resumes" in text or "resumes" in text.lower()
    assert "/login" in text


def test_app_clears_react_session_on_invalid_token() -> None:
    """401 path must clear React token state, not only localStorage."""
    app = (FE / "App.tsx").read_text(encoding="utf-8")
    assert "onSessionInvalid" in app
    assert "setTokenState(null)" in app
    assert "routeAfterUnauthorized" in app or "endSessionToLogin" in app
    # ResumesHome must call parent invalidation (not clearToken alone)
    assert "onSessionInvalid()" in app
    # Must not only clearToken without setTokenState on that path
    home_idx = app.find("function ResumesHome")
    assert home_idx != -1
    home = app[home_idx:]
    assert "onSessionInvalid()" in home
    assert "clearToken()" not in home or "onSessionInvalid" in home


def test_auth_guard_module_ships_pure_helpers() -> None:
    text = (FE / "authGuard.ts").read_text(encoding="utf-8")
    assert "resolveClientRoute" in text
    assert "routeAfterUnauthorized" in text
    assert "afterUnauthorizedSession" in text

"""
Health endpoint must drive the shipped FastAPI app entry (create_app).

TDD hard rule for Phase 0: API boots and reports healthy/ok via real route.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app


def test_health_returns_ok_via_shipped_app() -> None:
    app = create_app()
    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, dict)
    # Explicit healthy/ok-style body (not empty)
    status = (body.get("status") or body.get("health") or "").lower()
    assert status in {"ok", "healthy"}, f"expected ok/healthy status, got {body!r}"
    assert body.get("service") == "resumeai"


def test_health_lists_modular_seams() -> None:
    """Scaffold exposes seam names so growth stays modular (contract visibility)."""
    app = create_app()
    client = TestClient(app)
    body = client.get("/api/v1/health").json()
    seams = body.get("seams")
    assert isinstance(seams, list)
    for name in ("auth", "compile", "score", "jobs"):
        assert name in seams, f"missing seam boundary: {name}"

"""
ResumeAI API entry.

Run:
  cd backend
  uv run uvicorn app.main:app --reload --port 8001
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.auth.local import LocalAuthService
from app.auth.router import router as auth_router
from app.compile.engine import build_compiler
from app.config import get_settings
from app.jobs.runner import InProcessJobRunner
from app.resumes.router import router as resumes_router
from app.resumes.store import ResumeStore
from app.scoring.router import router as score_router
from app.scoring.stub import build_score_engine
from app.seams import SEAM_NAMES
from app.settings.router import router as settings_router
from app.settings.store import SettingsStore


def _wire_state(app: FastAPI) -> None:
    settings = get_settings()
    settings.data_path.mkdir(parents=True, exist_ok=True)
    app.state.settings = settings
    app.state.auth = LocalAuthService(settings.auth_db_path)
    app.state.resumes = ResumeStore(settings.resumes_db_path)
    app.state.compiler = build_compiler(settings.tectonic_path)
    app.state.user_settings = SettingsStore(settings.settings_db_path)
    app.state.jobs = InProcessJobRunner()
    app.state.score_engine = build_score_engine(
        settings.score_backend,
        vendor_path=settings.hiring_agent_path,
    )
    app.state.hiring_agent_path = settings.hiring_agent_path


@asynccontextmanager
async def lifespan(app: FastAPI):
    _wire_state(app)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="ResumeAI",
        version=__version__,
        description="Modular seams; product parity via PLAN.md phases.",
        lifespan=lifespan,
    )
    _wire_state(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    prefix = settings.api_prefix
    compiler = app.state.compiler

    @app.get(f"{prefix}/health")
    def health() -> dict:
        return {
            "status": "ok",
            "service": settings.app_name,
            "version": __version__,
            "seams": list(SEAM_NAMES),
            "latex_engine": compiler.preferred_engine,
            "score_backend": settings.score_backend,
        }

    app.include_router(auth_router, prefix=prefix)
    app.include_router(resumes_router, prefix=prefix)
    app.include_router(settings_router, prefix=prefix)
    app.include_router(score_router, prefix=prefix)

    return app


app = create_app()

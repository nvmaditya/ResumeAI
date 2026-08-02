"""Env-driven settings. Loads backend/.env when present."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parents[1]
_ENV_FILE = _BACKEND_DIR / ".env"


def _load_dotenv(path: Path) -> None:
    """Minimal .env loader — does not override existing process env."""
    if not path.is_file():
        return
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if not key:
            continue
        if key not in os.environ:
            os.environ[key] = val


def _default_hiring_agent_path() -> str:
    here = Path(__file__).resolve()
    monorepo = here.parents[3] / "backend" / "vendor" / "hiring-agent"
    local = here.parents[1] / "vendor" / "hiring-agent"
    if monorepo.is_dir():
        return str(monorepo)
    if local.is_dir():
        return str(local)
    return str(monorepo)


def _default_tectonic() -> str | None:
    tec = (os.environ.get("TECTONIC_PATH") or "").strip()
    if tec:
        return tec
    here = Path(__file__).resolve()
    mono = here.parents[3] / "backend" / "bin" / "tectonic.exe"
    if mono.is_file():
        return str(mono)
    local = _BACKEND_DIR / "bin" / "tectonic.exe"
    if local.is_file():
        return str(local)
    return None


@dataclass(frozen=True)
class Settings:
    app_name: str = "resumeai"
    app_env: str = "local"
    api_prefix: str = "/api/v1"
    cors_origins: tuple[str, ...] = ("http://localhost:5173", "http://127.0.0.1:5173")
    data_dir: str = "data"
    tectonic_path: str | None = None
    score_backend: str = "hiring_agent"  # hiring_agent | stub
    hiring_agent_path: str = ""

    @property
    def data_path(self) -> Path:
        p = Path(self.data_dir)
        if not p.is_absolute():
            return (_BACKEND_DIR / p).resolve()
        return p.resolve()

    @property
    def auth_db_path(self) -> Path:
        return self.data_path / "auth.db"

    @property
    def resumes_db_path(self) -> Path:
        return self.data_path / "resumes.db"

    @property
    def settings_db_path(self) -> Path:
        return self.data_path / "settings.db"


@lru_cache
def get_settings() -> Settings:
    _load_dotenv(_ENV_FILE)
    mono_env = Path(__file__).resolve().parents[3] / "backend" / ".env"
    if mono_env.is_file() and mono_env.resolve() != _ENV_FILE.resolve():
        _load_dotenv(mono_env)

    origins = os.environ.get(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    )
    ha = os.environ.get("HIRING_AGENT_PATH") or _default_hiring_agent_path()
    data_dir = os.environ.get("DATA_DIR", "data")
    return Settings(
        app_name=os.environ.get("APP_NAME", "resumeai"),
        app_env=os.environ.get("APP_ENV", "local"),
        api_prefix=os.environ.get("API_PREFIX", "/api/v1"),
        cors_origins=tuple(o.strip() for o in origins.split(",") if o.strip()),
        data_dir=data_dir,
        tectonic_path=_default_tectonic(),
        score_backend=os.environ.get("SCORE_BACKEND", "hiring_agent"),
        hiring_agent_path=ha,
    )

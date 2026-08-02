"""Authenticated settings + GitHub cache refresh."""

from __future__ import annotations

import os
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.auth.deps import get_current_user
from app.auth.local import SessionUser
from app.github.cache import format_cache_status, refresh_github
from app.settings.store import SettingsStore, build_stub_github_cache

router = APIRouter(prefix="/settings", tags=["settings"])


def get_settings_store(request: Request) -> SettingsStore:
    store = getattr(request.app.state, "user_settings", None)
    if store is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Settings store not configured",
        )
    return store


class SettingsPatch(BaseModel):
    github_username: str | None = Field(default=None, max_length=80)


@router.get("")
def get_settings(
    user: Annotated[SessionUser, Depends(get_current_user)],
    store: Annotated[SettingsStore, Depends(get_settings_store)],
) -> dict[str, Any]:
    out = store.get(user.id)
    out["email"] = user.email
    return out


@router.patch("")
def patch_settings(
    body: SettingsPatch,
    user: Annotated[SessionUser, Depends(get_current_user)],
    store: Annotated[SettingsStore, Depends(get_settings_store)],
) -> dict[str, Any]:
    if body.github_username is not None:
        out = store.set_username(user.id, body.github_username)
    else:
        out = store.get(user.id)
    out["email"] = user.email
    return out


@router.post("/github/update")
def update_github_cache(
    request: Request,
    user: Annotated[SessionUser, Depends(get_current_user)],
    store: Annotated[SettingsStore, Depends(get_settings_store)],
) -> dict[str, Any]:
    cur = store.get(user.id)
    uname = (cur.get("github_username") or "").strip()
    if not uname:
        raise HTTPException(
            status_code=400,
            detail="Set a GitHub username first",
        )
    vendor = getattr(request.app.state, "hiring_agent_path", None) or ""
    try:
        # Live fetch once via hiring-agent vendor (monorepo parity); store snapshot
        cache = refresh_github(uname, vendor_path=vendor)
    except Exception as exc:
        # Offline / rate-limit: honest stub snapshot so score can still use cache shape
        if os.environ.get("GITHUB_CACHE_STUB", "").lower() in ("1", "true", "yes"):
            cache = build_stub_github_cache(uname)
            cache["source"] = "stub_fallback"
            cache["error"] = str(exc)[:200]
        else:
            # still store stub so UX isn't blocked, but surface warning in status
            cache = build_stub_github_cache(uname)
            cache["source"] = "stub_fallback"
            cache["fetch_error"] = str(exc)[:300]
    out = store.set_cache(user.id, cache)
    out["email"] = user.email
    out["ok"] = True
    out["cache"] = out.get("github_cache")
    out["cache_status"] = format_cache_status(
        username=uname,
        cache=out.get("github_cache"),
        updated_at=out.get("cache_updated_at"),
    )
    return out

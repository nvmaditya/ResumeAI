"""FastAPI dependencies for the auth seam."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.local import LocalAuthService, SessionUser

_bearer = HTTPBearer(auto_error=False)


def get_auth_service(request: Request) -> LocalAuthService:
    auth = getattr(request.app.state, "auth", None)
    if auth is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Auth service not configured",
        )
    return auth


def get_current_user(
    request: Request,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    auth: Annotated[LocalAuthService, Depends(get_auth_service)],
) -> SessionUser:
    if creds is None or creds.scheme.lower() != "bearer" or not creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = auth.resolve_token(creds.credentials)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
            headers={"WWW-Authenticate": "Bearer"},
        )
    request.state.user = user
    request.state.token = creds.credentials
    return user

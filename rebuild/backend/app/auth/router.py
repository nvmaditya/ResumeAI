"""Auth HTTP routes — email/password + bearer session."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field

from app.auth.deps import get_auth_service, get_current_user
from app.auth.local import AuthError, LocalAuthService, SessionUser

router = APIRouter(prefix="/auth", tags=["auth"])
_bearer = HTTPBearer(auto_error=False)


class RegisterBody(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)  # service enforces ≥8 with product message


class LoginBody(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    email: str
    user_id: str


@router.post("/register", response_model=TokenOut)
def register(
    body: RegisterBody,
    auth: Annotated[LocalAuthService, Depends(get_auth_service)],
) -> dict:
    try:
        return auth.register(body.email, body.password)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/login", response_model=TokenOut)
def login(
    body: LoginBody,
    auth: Annotated[LocalAuthService, Depends(get_auth_service)],
) -> dict:
    try:
        return auth.login(body.email, body.password)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    auth: Annotated[LocalAuthService, Depends(get_auth_service)],
) -> None:
    token = None
    if creds and creds.credentials:
        token = creds.credentials
    elif getattr(request.state, "token", None):
        token = request.state.token
    if token:
        auth.logout(token)
    return None


@router.get("/me")
def me(user: Annotated[SessionUser, Depends(get_current_user)]) -> dict:
    return {"id": user.id, "email": user.email}

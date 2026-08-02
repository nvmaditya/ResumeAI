"""Local SQLite-backed auth — register/login/session."""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass
from pathlib import Path

from app.auth.passwords import hash_password, verify_password

MIN_PASSWORD_LEN = 8


class AuthError(Exception):
    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass(frozen=True)
class SessionUser:
    id: str
    email: str


class LocalAuthService:
    def __init__(self, db_path: Path) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                );
                """
            )

    def register(self, email: str, password: str) -> dict:
        email_n = (email or "").strip().lower()
        if not email_n or "@" not in email_n:
            raise AuthError("Invalid email", status_code=400)
        if len(password or "") < MIN_PASSWORD_LEN:
            raise AuthError(
                f"Password must be at least {MIN_PASSWORD_LEN} characters",
                status_code=400,
            )
        user_id = str(uuid.uuid4())
        pw_hash = hash_password(password)
        with self._connect() as conn:
            try:
                conn.execute(
                    "INSERT INTO users (id, email, password_hash) VALUES (?, ?, ?)",
                    (user_id, email_n, pw_hash),
                )
            except sqlite3.IntegrityError as exc:
                raise AuthError("Email already registered", status_code=400) from exc
            token = self._issue_token(conn, user_id)
            conn.commit()
        return {
            "access_token": token,
            "token_type": "bearer",
            "email": email_n,
            "user_id": user_id,
        }

    def login(self, email: str, password: str) -> dict:
        email_n = (email or "").strip().lower()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, password_hash FROM users WHERE email = ?",
                (email_n,),
            ).fetchone()
            if row is None or not verify_password(password or "", row["password_hash"]):
                raise AuthError("Invalid credentials", status_code=401)
            token = self._issue_token(conn, row["id"])
            conn.commit()
        return {
            "access_token": token,
            "token_type": "bearer",
            "email": email_n,
            "user_id": row["id"],
        }

    def logout(self, token: str) -> None:
        if not token:
            return
        with self._connect() as conn:
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()

    def resolve_token(self, token: str) -> SessionUser | None:
        if not token:
            return None
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT u.id AS id, u.email AS email
                FROM sessions s
                JOIN users u ON u.id = s.user_id
                WHERE s.token = ?
                """,
                (token,),
            ).fetchone()
        if row is None:
            return None
        return SessionUser(id=row["id"], email=row["email"])

    def _issue_token(self, conn: sqlite3.Connection, user_id: str) -> str:
        token = uuid.uuid4().hex + uuid.uuid4().hex
        conn.execute(
            "INSERT INTO sessions (token, user_id) VALUES (?, ?)",
            (token, user_id),
        )
        return token

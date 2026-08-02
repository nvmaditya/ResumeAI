"""User settings + GitHub cache (user-scoped SQLite)."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.github.cache import format_cache_status


class SettingsStore:
    def __init__(self, db_path: Path) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id TEXT PRIMARY KEY,
                    github_username TEXT NOT NULL DEFAULT '',
                    github_cache_json TEXT,
                    cache_updated_at TEXT,
                    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )

    def get(self, user_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM user_settings WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        if row is None:
            return {
                "github_username": "",
                "github_cache": None,
                "cache_updated_at": None,
                "cache_status": "No GitHub cache yet — Update GitHub data in Settings.",
            }
        cache = None
        if row["github_cache_json"]:
            try:
                cache = json.loads(row["github_cache_json"])
            except json.JSONDecodeError:
                cache = None
        uname = row["github_username"] or ""
        return {
            "github_username": uname,
            "github_cache": cache,
            "cache_updated_at": row["cache_updated_at"],
            "cache_status": format_cache_status(
                username=uname,
                cache=cache,
                updated_at=row["cache_updated_at"],
            ),
        }

    def set_username(self, user_id: str, username: str) -> dict[str, Any]:
        uname = (username or "").strip().lstrip("@")
        cur = self.get(user_id)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO user_settings (user_id, github_username, github_cache_json, cache_updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    github_username = excluded.github_username,
                    updated_at = datetime('now')
                """,
                (
                    user_id,
                    uname,
                    json.dumps(cur["github_cache"]) if cur["github_cache"] else None,
                    cur["cache_updated_at"],
                ),
            )
            conn.commit()
        return self.get(user_id)

    def set_cache(self, user_id: str, cache: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        cur = self.get(user_id)
        uname = cur["github_username"] or str(cache.get("login") or "")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO user_settings (user_id, github_username, github_cache_json, cache_updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    github_cache_json = excluded.github_cache_json,
                    cache_updated_at = excluded.cache_updated_at,
                    github_username = COALESCE(NULLIF(user_settings.github_username, ''), excluded.github_username),
                    updated_at = datetime('now')
                """,
                (user_id, uname, json.dumps(cache), now),
            )
            conn.commit()
        return self.get(user_id)


def build_stub_github_cache(username: str) -> dict[str, Any]:
    """Offline snapshot when live GitHub fetch fails — still cache-only for score."""
    uname = (username or "").strip().lstrip("@") or "user"
    repos = [
        {"name": f"{uname}-resume", "stars": 1, "language": "Python"},
        {"name": f"{uname}-notes", "stars": 0, "language": "Markdown"},
    ]
    return {
        "login": uname,
        "username": uname,
        "repo_count": len(repos),
        "total_repos": len(repos),
        "repos": repos,
        "profile": {"username": uname},
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "stub",
    }

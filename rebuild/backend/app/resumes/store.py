"""User-scoped resume persistence (SQLite)."""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.resumes.defaults import (
    DEFAULT_AI_TITLE,
    DEFAULT_LATEX_TITLE,
    EMPTY_FORM,
    STARTER_LATEX,
)
from app.resumes.mode import workspace_mode_for_track
from app.resumes.versions import latex_unchanged, normalize_message


@dataclass
class ResumeRecord:
    id: str
    user_id: str
    title: str
    track: str
    tags: list[str]
    form: dict[str, Any] | None
    latex_source: str | None

    def to_dict(self, *, list_view: bool = False) -> dict[str, Any]:
        mode = workspace_mode_for_track(self.track)
        base = {
            "id": self.id,
            "title": self.title,
            "track": self.track,
            "tags": list(self.tags),
            **mode,
        }
        if list_view:
            return base
        base["form"] = self.form
        base["latex_source"] = self.latex_source
        return base


@dataclass
class CheckpointRecord:
    id: str
    resume_id: str
    message: str
    latex_source: str
    created_at: str

    def to_dict(self, *, include_source: bool = True) -> dict[str, Any]:
        out: dict[str, Any] = {
            "id": self.id,
            "resume_id": self.resume_id,
            "message": self.message,
            "created_at": self.created_at,
        }
        if include_source:
            out["latex_source"] = self.latex_source
        return out


class ResumeStore:
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
                CREATE TABLE IF NOT EXISTS resumes (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    track TEXT NOT NULL,
                    tags_json TEXT NOT NULL DEFAULT '[]',
                    form_json TEXT,
                    latex_source TEXT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_resumes_user ON resumes(user_id)"
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS resume_checkpoints (
                    id TEXT PRIMARY KEY,
                    resume_id TEXT NOT NULL,
                    message TEXT NOT NULL,
                    latex_source TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_checkpoints_resume "
                "ON resume_checkpoints(resume_id, created_at DESC)"
            )

    def create(self, user_id: str, kind: str) -> ResumeRecord:
        kind_n = (kind or "").strip().lower()
        rid = str(uuid.uuid4())
        if kind_n == "ai":
            rec = ResumeRecord(
                id=rid,
                user_id=user_id,
                title=DEFAULT_AI_TITLE,
                track="structured",
                tags=[],
                form=json.loads(json.dumps(EMPTY_FORM)),
                latex_source=None,
            )
        elif kind_n == "latex":
            rec = ResumeRecord(
                id=rid,
                user_id=user_id,
                title=DEFAULT_LATEX_TITLE,
                track="latex",
                tags=[],
                form=None,
                latex_source=STARTER_LATEX,
            )
        else:
            raise ValueError(f"unsupported create kind: {kind}")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO resumes (id, user_id, title, track, tags_json, form_json, latex_source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rec.id,
                    rec.user_id,
                    rec.title,
                    rec.track,
                    json.dumps(rec.tags),
                    json.dumps(rec.form) if rec.form is not None else None,
                    rec.latex_source,
                ),
            )
            conn.commit()
        return rec

    def list_for_user(
        self,
        user_id: str,
        *,
        q: str | None = None,
        tags: list[str] | None = None,
    ) -> list[ResumeRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM resumes WHERE user_id = ? ORDER BY updated_at DESC",
                (user_id,),
            ).fetchall()
        items = [self._row(r) for r in rows]
        qn = (q or "").strip().lower()
        if qn:
            items = [
                r
                for r in items
                if qn in r.title.lower()
                or qn in r.track.lower()
                or any(qn in t.lower() for t in r.tags)
            ]
        wanted = [t.strip().lower() for t in (tags or []) if t.strip()]
        if wanted:
            items = [
                r
                for r in items
                if all(w in [t.lower() for t in r.tags] for w in wanted)
            ]
        return items

    def get(self, user_id: str, resume_id: str) -> ResumeRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM resumes WHERE id = ? AND user_id = ?",
                (resume_id, user_id),
            ).fetchone()
        return self._row(row) if row else None

    def delete(self, user_id: str, resume_id: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute(
                "DELETE FROM resumes WHERE id = ? AND user_id = ?",
                (resume_id, user_id),
            )
            conn.commit()
            return cur.rowcount > 0

    def update_meta(
        self,
        user_id: str,
        resume_id: str,
        *,
        title: str | None = None,
        tags: list[str] | None = None,
        form: dict[str, Any] | None = None,
        latex_source: str | None = None,
        track: str | None = None,
    ) -> ResumeRecord | None:
        """Persist identity + body (+ optional track flip). Fields only update when not None."""
        rec = self.get(user_id, resume_id)
        if rec is None:
            return None
        if title is not None:
            rec.title = title.strip() or rec.title
        if tags is not None:
            rec.tags = [str(t).strip() for t in tags if str(t).strip()]
        if form is not None:
            rec.form = form
        if latex_source is not None:
            rec.latex_source = latex_source
        if track is not None:
            t = track.strip().lower()
            if t in ("structured", "latex"):
                rec.track = t
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE resumes
                SET title = ?, tags_json = ?, form_json = ?, latex_source = ?,
                    track = ?, updated_at = datetime('now')
                WHERE id = ? AND user_id = ?
                """,
                (
                    rec.title,
                    json.dumps(rec.tags),
                    json.dumps(rec.form) if rec.form is not None else None,
                    rec.latex_source,
                    rec.track,
                    rec.id,
                    user_id,
                ),
            )
            conn.commit()
        return rec

    def _row(self, row: sqlite3.Row) -> ResumeRecord:
        form_raw = row["form_json"]
        form = json.loads(form_raw) if form_raw else None
        tags = json.loads(row["tags_json"] or "[]")
        return ResumeRecord(
            id=row["id"],
            user_id=row["user_id"],
            title=row["title"],
            track=row["track"],
            tags=list(tags),
            form=form,
            latex_source=row["latex_source"],
        )

    def _cp_row(self, row: sqlite3.Row) -> CheckpointRecord:
        return CheckpointRecord(
            id=row["id"],
            resume_id=row["resume_id"],
            message=row["message"],
            latex_source=row["latex_source"] or "",
            created_at=row["created_at"],
        )

    def list_checkpoints(
        self, user_id: str, resume_id: str
    ) -> list[CheckpointRecord] | None:
        """Return checkpoints newest-first, or None if resume not owned."""
        if self.get(user_id, resume_id) is None:
            return None
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM resume_checkpoints
                WHERE resume_id = ?
                ORDER BY created_at DESC, id DESC
                """,
                (resume_id,),
            ).fetchall()
        return [self._cp_row(r) for r in rows]

    def commit_checkpoint(
        self, user_id: str, resume_id: str, message: str | None = None
    ) -> dict[str, Any] | None:
        """
        Snapshot live latex. Unchanged vs latest → no-op.
        Returns None if resume not found; else commit result dict.
        """
        rec = self.get(user_id, resume_id)
        if rec is None:
            return None
        live = rec.latex_source or ""
        latest = self._latest_checkpoint_raw(resume_id)
        if latest is not None and latex_unchanged(live, latest.latex_source):
            return {
                "committed": False,
                "unchanged": True,
                "message": "No changes since last commit",
            }
        msg = normalize_message(message)
        cid = str(uuid.uuid4())
        # Sub-second timestamps so same-second commits order correctly
        created = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO resume_checkpoints
                    (id, resume_id, message, latex_source, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (cid, resume_id, msg, live, created),
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM resume_checkpoints WHERE id = ?", (cid,)
            ).fetchone()
        cp = self._cp_row(row)
        return {
            "committed": True,
            "unchanged": False,
            "message": "Version saved",
            "checkpoint": cp.to_dict(include_source=True),
        }

    def _latest_checkpoint_raw(self, resume_id: str) -> CheckpointRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM resume_checkpoints
                WHERE resume_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """,
                (resume_id,),
            ).fetchone()
        return self._cp_row(row) if row else None

    def get_checkpoint(
        self, user_id: str, resume_id: str, checkpoint_id: str
    ) -> CheckpointRecord | None:
        if self.get(user_id, resume_id) is None:
            return None
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM resume_checkpoints
                WHERE id = ? AND resume_id = ?
                """,
                (checkpoint_id, resume_id),
            ).fetchone()
        return self._cp_row(row) if row else None

    def restore_checkpoint(
        self, user_id: str, resume_id: str, checkpoint_id: str
    ) -> ResumeRecord | None:
        """Replace live latex_source with checkpoint; does not touch form/track."""
        cp = self.get_checkpoint(user_id, resume_id, checkpoint_id)
        if cp is None:
            # distinguish resume-missing vs checkpoint-missing via get
            if self.get(user_id, resume_id) is None:
                return None
            raise KeyError("checkpoint not found")
        return self.update_meta(
            user_id, resume_id, latex_source=cp.latex_source
        )

    def delete_checkpoint(
        self, user_id: str, resume_id: str, checkpoint_id: str
    ) -> bool | None:
        """
        Delete checkpoint only. None = resume not found;
        False = checkpoint missing; True = deleted.
        """
        if self.get(user_id, resume_id) is None:
            return None
        with self._connect() as conn:
            cur = conn.execute(
                """
                DELETE FROM resume_checkpoints
                WHERE id = ? AND resume_id = ?
                """,
                (checkpoint_id, resume_id),
            )
            conn.commit()
            return cur.rowcount > 0

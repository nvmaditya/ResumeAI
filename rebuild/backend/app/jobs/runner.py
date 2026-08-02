"""In-process JobRunner — queued → processing → complete|failed."""

from __future__ import annotations

import threading
import uuid
from typing import Any, Callable


class InProcessJobRunner:
    def __init__(self) -> None:
        self._jobs: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def enqueue(
        self,
        kind: str,
        payload: dict[str, Any],
        handler: Callable[[dict[str, Any]], Any],
        *,
        user_id: str | None = None,
    ) -> str:
        jid = str(uuid.uuid4())
        with self._lock:
            self._jobs[jid] = {
                "id": jid,
                "job_id": jid,
                "kind": kind,
                "status": "queued",
                "payload": payload,
                "result": None,
                "error": None,
                "user_id": user_id,
            }

        def _run() -> None:
            with self._lock:
                job = self._jobs.get(jid)
                if not job:
                    return
                job["status"] = "processing"
            try:
                result = handler(payload)
                with self._lock:
                    job = self._jobs.get(jid)
                    if job:
                        job["status"] = "complete"
                        job["result"] = result
            except Exception as exc:  # noqa: BLE001 — surface job failure
                with self._lock:
                    job = self._jobs.get(jid)
                    if job:
                        job["status"] = "failed"
                        job["error"] = str(exc) or "job failed"
                        job["result"] = None

        # Run inline for deterministic tests; still transitions states
        with self._lock:
            self._jobs[jid]["status"] = "processing"
        try:
            result = handler(payload)
            with self._lock:
                self._jobs[jid]["status"] = "complete"
                self._jobs[jid]["result"] = result
        except Exception as exc:  # noqa: BLE001
            with self._lock:
                self._jobs[jid]["status"] = "failed"
                self._jobs[jid]["error"] = str(exc) or "job failed"
        return jid

    def get(self, job_id: str, *, user_id: str | None = None) -> dict[str, Any] | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            if user_id is not None and job.get("user_id") and job["user_id"] != user_id:
                return None
            return {
                "id": job["id"],
                "job_id": job["job_id"],
                "kind": job["kind"],
                "status": job["status"],
                "result": job["result"],
                "error": job["error"],
            }

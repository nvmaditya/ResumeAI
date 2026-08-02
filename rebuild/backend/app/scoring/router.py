"""Score start + job poll endpoints."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.auth.deps import get_current_user
from app.auth.local import SessionUser
from app.jobs.runner import InProcessJobRunner
from app.resumes.store import ResumeStore
from app.settings.store import SettingsStore

router = APIRouter(tags=["score"])


def get_resume_store(request: Request) -> ResumeStore:
    store = getattr(request.app.state, "resumes", None)
    if store is None:
        raise HTTPException(status_code=500, detail="Resume store not configured")
    return store


def get_settings_store(request: Request) -> SettingsStore:
    store = getattr(request.app.state, "user_settings", None)
    if store is None:
        raise HTTPException(status_code=500, detail="Settings store not configured")
    return store


def get_jobs(request: Request) -> InProcessJobRunner:
    jobs = getattr(request.app.state, "jobs", None)
    if jobs is None:
        raise HTTPException(status_code=500, detail="Job runner not configured")
    return jobs


def get_score_engine(request: Request) -> Any:
    eng = getattr(request.app.state, "score_engine", None)
    if eng is None:
        raise HTTPException(status_code=500, detail="Score engine not configured")
    return eng


class ScoreBody(BaseModel):
    jd: str | None = Field(default=None, max_length=4000)


@router.post("/resumes/{resume_id}/score")
def start_score(
    resume_id: str,
    body: ScoreBody,
    user: Annotated[SessionUser, Depends(get_current_user)],
    resumes: Annotated[ResumeStore, Depends(get_resume_store)],
    settings_store: Annotated[SettingsStore, Depends(get_settings_store)],
    jobs: Annotated[InProcessJobRunner, Depends(get_jobs)],
    engine: Annotated[Any, Depends(get_score_engine)],
) -> dict[str, Any]:
    rec = resumes.get(user.id, resume_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Resume text: latex source preferred; form summary fallback
    text_parts: list[str] = []
    if rec.latex_source:
        text_parts.append(rec.latex_source)
    if rec.form and isinstance(rec.form, dict):
        basics = rec.form.get("basics") if isinstance(rec.form.get("basics"), dict) else {}
        if basics:
            text_parts.append(
                " ".join(
                    str(basics.get(k) or "")
                    for k in ("name", "summary", "email")
                )
            )
        for key in ("experience", "education", "projects", "skills"):
            text_parts.append(str(rec.form.get(key) or ""))
    resume_text = "\n".join(text_parts)

    # Cache only from settings — never live GitHub
    s = settings_store.get(user.id)
    github_cache = s.get("github_cache")

    def handler(payload: dict[str, Any]) -> dict[str, Any]:
        # Cache-only GitHub; light JD sanitize (no live fetch)
        jd = (payload.get("jd") or "") or None
        if isinstance(jd, str):
            jd = jd.strip()[:4000]
            jd = "".join(ch for ch in jd if ch in "\n\t" or ord(ch) >= 32) or None
        return engine.score(
            payload["resume_text"] or "",
            jd=jd,
            github_cache=payload.get("github_cache"),
        )

    jid = jobs.enqueue(
        "score",
        {
            "resume_id": resume_id,
            "resume_text": resume_text,
            "jd": body.jd,
            "github_cache": github_cache,
        },
        handler,
        user_id=user.id,
    )
    job = jobs.get(jid, user_id=user.id) or {
        "job_id": jid,
        "status": "queued",
    }
    return {
        "job_id": jid,
        "id": jid,
        "status": job.get("status", "queued"),
        "result": job.get("result"),
    }


@router.get("/jobs/{job_id}")
def get_job(
    job_id: str,
    user: Annotated[SessionUser, Depends(get_current_user)],
    jobs: Annotated[InProcessJobRunner, Depends(get_jobs)],
) -> dict[str, Any]:
    job = jobs.get(job_id, user_id=user.id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

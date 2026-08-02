"""Protected resume list/create/get/delete + compile/lint/downloads."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any, Literal
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import Response
from pydantic import BaseModel

from app.auth.deps import get_current_user
from app.auth.local import SessionUser
from app.compile.engine import CompositeCompiler
from app.compile.lint import lint_latex
from app.generate.form_to_latex import form_to_latex
from app.generate.service import generate_from_form
from app.resumes.store import ResumeStore

router = APIRouter(prefix="/resumes", tags=["resumes"])


def get_resume_store(request: Request) -> ResumeStore:
    store = getattr(request.app.state, "resumes", None)
    if store is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Resume store not configured",
        )
    return store


def get_compiler(request: Request) -> CompositeCompiler:
    c = getattr(request.app.state, "compiler", None)
    if c is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Compiler not configured",
        )
    return c


def _pdf_path(request: Request, user_id: str, resume_id: str) -> Path:
    settings = request.app.state.settings
    root = Path(settings.data_path) / "pdfs" / user_id
    root.mkdir(parents=True, exist_ok=True)
    return root / f"{resume_id}.pdf"


def _safe_filename(title: str, ext: str) -> str:
    base = "".join(c if c.isalnum() or c in " -_" else "_" for c in (title or "resume"))
    base = base.strip() or "resume"
    return f"{base[:80]}.{ext}"


class CreateBody(BaseModel):
    create: Literal["ai", "latex"]


class PatchBody(BaseModel):
    title: str | None = None
    tags: list[str] | None = None
    form: dict[str, Any] | None = None
    latex_source: str | None = None


class CommitVersionBody(BaseModel):
    message: str | None = None


@router.get("")
def list_resumes(
    user: Annotated[SessionUser, Depends(get_current_user)],
    store: Annotated[ResumeStore, Depends(get_resume_store)],
    q: str | None = Query(default=None),
    tags: str | None = Query(
        default=None,
        description="Comma-separated tags; AND-matched",
    ),
) -> list[dict[str, Any]]:
    tag_list = [t.strip() for t in (tags or "").split(",") if t.strip()]
    rows = store.list_for_user(user.id, q=q, tags=tag_list or None)
    return [r.to_dict(list_view=True) for r in rows]


@router.post("")
def create_resume(
    body: CreateBody,
    user: Annotated[SessionUser, Depends(get_current_user)],
    store: Annotated[ResumeStore, Depends(get_resume_store)],
) -> dict[str, Any]:
    try:
        rec = store.create(user.id, body.create)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return rec.to_dict(list_view=False)


@router.get("/{resume_id}")
def get_resume(
    resume_id: str,
    user: Annotated[SessionUser, Depends(get_current_user)],
    store: Annotated[ResumeStore, Depends(get_resume_store)],
) -> dict[str, Any]:
    rec = store.get(user.id, resume_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    return rec.to_dict(list_view=False)


@router.patch("/{resume_id}")
def patch_resume(
    resume_id: str,
    body: PatchBody,
    user: Annotated[SessionUser, Depends(get_current_user)],
    store: Annotated[ResumeStore, Depends(get_resume_store)],
) -> dict[str, Any]:
    rec = store.update_meta(
        user.id,
        resume_id,
        title=body.title,
        tags=body.tags,
        form=body.form,
        latex_source=body.latex_source,
    )
    if rec is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    return rec.to_dict(list_view=False)


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(
    resume_id: str,
    user: Annotated[SessionUser, Depends(get_current_user)],
    store: Annotated[ResumeStore, Depends(get_resume_store)],
) -> None:
    if not store.delete(user.id, resume_id):
        raise HTTPException(status_code=404, detail="Resume not found")
    return None


@router.post("/{resume_id}/generate")
def generate_resume(
    resume_id: str,
    request: Request,
    user: Annotated[SessionUser, Depends(get_current_user)],
    store: Annotated[ResumeStore, Depends(get_resume_store)],
    compiler: Annotated[CompositeCompiler, Depends(get_compiler)],
) -> dict[str, Any]:
    """
    Legacy form→LaTeX helper. Product UI removed AI Generate; Compile owns form→PDF.
    Does **not** flip track (form path stays structured). Prefer POST .../compile.
    """
    rec = store.get(user.id, resume_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    if rec.track != "structured":
        raise HTTPException(
            status_code=400,
            detail="Generate only available on structured (form) path",
        )
    try:
        result = generate_from_form(rec.form, title=rec.title)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc) or "generate failed") from exc
    if result.error or not (result.latex or "").strip():
        raise HTTPException(
            status_code=400,
            detail=result.error or "generate produced empty LaTeX",
        )
    # Persist latex snapshot only — stay structured (form path pivot)
    saved = store.update_meta(
        user.id,
        resume_id,
        latex_source=result.latex,
    )
    if saved is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    out = saved.to_dict(list_view=False)
    out["used_llm"] = bool(result.used_llm)
    out["iterations"] = result.iterations
    out["diagnostics"] = result.diagnostics
    try:
        cre = compiler.compile_tex(
            result.latex,
            title=saved.title,
            track="structured",
            structured=saved.form,
        )
        if cre.ok and cre.pdf.startswith(b"%PDF") and cre.size >= 200:
            path = _pdf_path(request, user.id, resume_id)
            path.write_bytes(cre.pdf)
            out["compile_engine"] = cre.engine
            out["compile_size"] = cre.size
    except Exception:
        pass
    return out


@router.post("/{resume_id}/compile")
def compile_resume(
    resume_id: str,
    request: Request,
    user: Annotated[SessionUser, Depends(get_current_user)],
    store: Annotated[ResumeStore, Depends(get_resume_store)],
    compiler: Annotated[CompositeCompiler, Depends(get_compiler)],
) -> dict[str, Any]:
    """
    LATEX_ONLY: source → PDF.
    FORM_PATH (structured): deterministic form → LaTeX snapshot + PDF; track stays structured.
    """
    rec = store.get(user.id, resume_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Resume not found")

    if rec.track == "structured":
        # Product: Compile owns form→LaTeX (deterministic) + PDF; form remains SoT
        try:
            source = form_to_latex(rec.form, title=rec.title)
        except Exception as exc:
            raise HTTPException(
                status_code=400, detail=str(exc) or "form→LaTeX failed"
            ) from exc
        if not (source or "").strip():
            raise HTTPException(status_code=400, detail="form produced empty LaTeX")
        saved = store.update_meta(user.id, resume_id, latex_source=source)
        if saved is None:
            raise HTTPException(status_code=404, detail="Resume not found")
        rec = saved
        result = compiler.compile_tex(
            source,
            title=rec.title,
            track="structured",
            structured=rec.form,
        )
    else:
        source = (rec.latex_source or "").strip()
        if not source:
            raise HTTPException(status_code=400, detail="empty source")
        result = compiler.compile_tex(
            source,
            title=rec.title,
            track=rec.track,
            structured=rec.form,
        )

    if not result.ok or not result.pdf.startswith(b"%PDF") or result.size < 200:
        raise HTTPException(
            status_code=400,
            detail=result.error or "compile failed",
        )
    path = _pdf_path(request, user.id, resume_id)
    path.write_bytes(result.pdf)
    return {
        "ok": True,
        "engine": result.engine,
        "size": result.size,
        "track": rec.track,
    }


@router.post("/{resume_id}/lint")
def lint_resume(
    resume_id: str,
    user: Annotated[SessionUser, Depends(get_current_user)],
    store: Annotated[ResumeStore, Depends(get_resume_store)],
) -> dict[str, Any]:
    rec = store.get(user.id, resume_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    source = rec.latex_source or ""
    diags = lint_latex(source, track=rec.track)
    return {"diagnostics": diags, "count": len(diags)}


@router.get("/{resume_id}/pdf")
def download_pdf(
    resume_id: str,
    request: Request,
    user: Annotated[SessionUser, Depends(get_current_user)],
    store: Annotated[ResumeStore, Depends(get_resume_store)],
) -> Response:
    rec = store.get(user.id, resume_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    path = _pdf_path(request, user.id, resume_id)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="PDF not compiled yet")
    data = path.read_bytes()
    if not data.startswith(b"%PDF") or len(data) < 200:
        path.unlink(missing_ok=True)
        raise HTTPException(status_code=409, detail="stored PDF invalid; recompile")
    fname = _safe_filename(rec.title, "pdf")
    return Response(
        content=data,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{fname}"; filename*=UTF-8\'\'{quote(fname)}'
        },
    )


@router.get("/{resume_id}/tex")
def download_tex(
    resume_id: str,
    user: Annotated[SessionUser, Depends(get_current_user)],
    store: Annotated[ResumeStore, Depends(get_resume_store)],
) -> Response:
    rec = store.get(user.id, resume_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    source = rec.latex_source or ""
    if not source.strip():
        raise HTTPException(status_code=404, detail="No LaTeX source")
    fname = _safe_filename(rec.title, "tex")
    return Response(
        content=source.encode("utf-8"),
        media_type="application/x-tex",
        headers={
            "Content-Disposition": f'attachment; filename="{fname}"; filename*=UTF-8\'\'{quote(fname)}'
        },
    )


# --- Phase 6: LaTeX version checkpoints ---


@router.get("/{resume_id}/versions")
def list_versions(
    resume_id: str,
    user: Annotated[SessionUser, Depends(get_current_user)],
    store: Annotated[ResumeStore, Depends(get_resume_store)],
) -> list[dict[str, Any]]:
    items = store.list_checkpoints(user.id, resume_id)
    if items is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    # Scannable rows: message + time; source omitted from list payload
    return [c.to_dict(include_source=False) for c in items]


@router.post("/{resume_id}/versions")
def commit_version(
    resume_id: str,
    body: CommitVersionBody,
    user: Annotated[SessionUser, Depends(get_current_user)],
    store: Annotated[ResumeStore, Depends(get_resume_store)],
) -> dict[str, Any]:
    result = store.commit_checkpoint(user.id, resume_id, body.message)
    if result is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    return result


@router.post("/{resume_id}/versions/{checkpoint_id}/restore")
def restore_version(
    resume_id: str,
    checkpoint_id: str,
    request: Request,
    user: Annotated[SessionUser, Depends(get_current_user)],
    store: Annotated[ResumeStore, Depends(get_resume_store)],
    compiler: Annotated[CompositeCompiler, Depends(get_compiler)],
) -> dict[str, Any]:
    try:
        rec = store.restore_checkpoint(user.id, resume_id, checkpoint_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Checkpoint not found") from None
    if rec is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    out = rec.to_dict(list_view=False)
    out["restored"] = True
    out["message"] = "Restored"
    # Quiet recompile so preview can refresh (do not fail restore on compile)
    source = (rec.latex_source or "").strip()
    if source:
        try:
            cre = compiler.compile_tex(
                source,
                title=rec.title,
                track=rec.track,
                structured=rec.form,
            )
            if cre.ok and cre.pdf.startswith(b"%PDF") and cre.size >= 200:
                path = _pdf_path(request, user.id, resume_id)
                path.write_bytes(cre.pdf)
                out["compile_engine"] = cre.engine
                out["compile_size"] = cre.size
        except Exception:
            pass
    return out


@router.delete(
    "/{resume_id}/versions/{checkpoint_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_version(
    resume_id: str,
    checkpoint_id: str,
    user: Annotated[SessionUser, Depends(get_current_user)],
    store: Annotated[ResumeStore, Depends(get_resume_store)],
) -> None:
    result = store.delete_checkpoint(user.id, resume_id, checkpoint_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    if result is False:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    return None

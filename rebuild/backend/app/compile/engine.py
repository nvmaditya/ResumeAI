"""Compile seam: tectonic preferred, layout fallback. Always valid %PDF on success."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.compile.assets import ensure_placeholder_images
from app.compile.layout import render_layout_pdf


def resolve_tectonic(tectonic_path: str | None = None) -> Path | None:
    candidates: list[Path] = []
    if tectonic_path:
        candidates.append(Path(tectonic_path))
    env = os.environ.get("TECTONIC_PATH")
    if env:
        candidates.append(Path(env))
    here = Path(__file__).resolve()
    # this package backend/app/compile → monorepo root parents[4] for shared tectonic binary
    monorepo_bin = here.parents[4] / "backend" / "bin" / "tectonic.exe"
    candidates.append(monorepo_bin)
    candidates.append(here.parents[4] / "backend" / "bin" / "tectonic")
    local = here.parents[2] / "bin" / "tectonic.exe"
    candidates.append(local)
    candidates.append(here.parents[2] / "bin" / "tectonic")
    # also walk up looking for backend/bin/tectonic.exe
    for parent in here.parents:
        candidates.append(parent / "backend" / "bin" / "tectonic.exe")
        candidates.append(parent / "bin" / "tectonic.exe")
    for p in candidates:
        try:
            if p.is_file():
                return p
        except OSError:
            continue
    which = shutil.which("tectonic") or shutil.which("tectonic.exe")
    return Path(which) if which else None


@dataclass
class CompileResult:
    ok: bool
    engine: str
    pdf: bytes
    error: str | None = None

    @property
    def size(self) -> int:
        return len(self.pdf)


class CompositeCompiler:
    def __init__(self, tectonic: Path | None = None) -> None:
        self._tectonic = tectonic

    @property
    def preferred_engine(self) -> str:
        return "tectonic" if self._tectonic else "layout"

    def compile_tex(
        self,
        source: str,
        *,
        title: str = "Resume",
        track: str = "latex",
        structured: dict[str, Any] | None = None,
    ) -> CompileResult:
        src = (source or "").strip()
        if track == "structured" and not src:
            from app.compile.layout import structured_to_blocks, build_pdf

            pdf = build_pdf(structured_to_blocks(structured, title))
            if pdf.startswith(b"%PDF") and len(pdf) >= 200:
                return CompileResult(ok=True, engine="layout", pdf=pdf)
            return CompileResult(
                ok=False, engine="layout", pdf=b"", error="empty structured resume"
            )

        if not src and not structured:
            return CompileResult(
                ok=False, engine=self.preferred_engine, pdf=b"", error="empty source"
            )

        tectonic_err: str | None = None
        if self._tectonic and src:
            try:
                pdf = self._run_tectonic(src)
                if pdf.startswith(b"%PDF") and len(pdf) >= 200:
                    return CompileResult(ok=True, engine="tectonic", pdf=pdf)
                tectonic_err = "tectonic produced invalid PDF"
            except Exception as exc:
                tectonic_err = str(exc) or "tectonic failed"

        # LaTeX track with real TeX: do not silent-fallback to layout garbage PDF
        complex_tex = bool(
            src
            and (
                r"\documentclass" in src
                or r"\usepackage" in src
                or r"\begin{document}" in src
            )
        )
        if track == "latex" and complex_tex and self._tectonic and tectonic_err:
            return CompileResult(
                ok=False,
                engine="tectonic",
                pdf=b"",
                error=(
                    "TeX compile failed (tectonic). Fix the source or run Lint.\n"
                    + tectonic_err[:1200]
                ),
            )
        if track == "latex" and complex_tex and not self._tectonic:
            return CompileResult(
                ok=False,
                engine="layout",
                pdf=b"",
                error=(
                    "No tectonic TeX engine found. Install tectonic or set TECTONIC_PATH "
                    "(e.g. monorepo backend/bin/tectonic.exe). Layout preview cannot "
                    "render full LaTeX packages."
                ),
            )

        try:
            pdf = render_layout_pdf(
                title=title, latex=src or None, structured=structured, track=track
            )
            return CompileResult(ok=True, engine="layout", pdf=pdf)
        except Exception as exc:
            err = str(exc) or "compile failed"
            if tectonic_err:
                err = f"{tectonic_err}; layout also failed: {err}"
            return CompileResult(
                ok=False, engine="layout", pdf=b"", error=err
            )

    def _run_tectonic(self, source: str) -> bytes:
        assert self._tectonic is not None
        with tempfile.TemporaryDirectory(prefix="resumeai-tex-") as tmp:
            tdir = Path(tmp)
            # Provide placeholders for missing \includegraphics{...} assets
            # (common: profile.jpg next to Overleaf projects)
            ensure_placeholder_images(source, tdir)
            tex_path = tdir / "main.tex"
            tex_path.write_text(source, encoding="utf-8")
            env = os.environ.copy()
            # Quiet common Windows fontconfig noise; not the real failure mode
            env.setdefault("FONTCONFIG_PATH", str(tdir))
            env.setdefault("FONTCONFIG_FILE", str(tdir / "fonts.conf"))
            (tdir / "fonts.conf").write_text(
                '<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM '
                '"urn:fontconfig:fonts.dtd"><fontconfig></fontconfig>\n',
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    str(self._tectonic),
                    "-X",
                    "compile",
                    "--outdir",
                    str(tdir),
                    str(tex_path),
                ],
                capture_output=True,
                timeout=120,
                check=False,
                cwd=str(tdir),
                env=env,
            )
            pdf_path = tdir / "main.pdf"
            if not pdf_path.is_file():
                pdfs = [p for p in tdir.glob("*.pdf") if p.name != "profile.pdf"]
                # ignore tiny placeholder pdfs if any
                pdfs = [p for p in pdfs if p.stat().st_size >= 200]
                if not pdfs:
                    err = (
                        proc.stderr.decode("utf-8", errors="replace")
                        or proc.stdout.decode("utf-8", errors="replace")
                    )
                    err = _friendly_tex_error(err)
                    raise RuntimeError(err[:1200] or "tectonic produced no pdf")
                pdf_path = max(pdfs, key=lambda p: p.stat().st_size)
            data = pdf_path.read_bytes()
            if not data.startswith(b"%PDF"):
                raise RuntimeError("tectonic output not a PDF")
            return data


def _friendly_tex_error(raw: str) -> str:
    """Strip fontconfig noise; highlight missing images / TeX errors."""
    lines = []
    for ln in (raw or "").splitlines():
        low = ln.lower()
        if "fontconfig" in low:
            continue
        if not ln.strip():
            continue
        lines.append(ln)
    text = "\n".join(lines).strip() or (raw or "").strip()
    if "unable to load picture" in text.lower() or "profile.jpg" in text.lower():
        text = (
            "Missing image file referenced by \\includegraphics "
            "(e.g. profile.jpg). A placeholder is injected automatically — "
            "if this still fails, check the path in your .tex.\n"
        ) + text
    return text


def build_compiler(tectonic_path: str | None = None) -> CompositeCompiler:
    return CompositeCompiler(resolve_tectonic(tectonic_path))

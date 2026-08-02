"""
Generate: seed form→LaTeX + lint-oriented repair loop + honest used_llm.

Deterministic template path only (used_llm=False). No live LLM in this MVP.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.compile.lint import lint_latex
from app.generate.form_to_latex import form_to_latex

MAX_REPAIR = 3


@dataclass
class GenerateResult:
    latex: str
    used_llm: bool
    iterations: int
    diagnostics: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None


def _repair_latex(tex: str, diags: list[dict[str, Any]]) -> str:
    """Deterministic structural repairs for common lint errors."""
    out = tex
    messages = " ".join(d.get("message", "") for d in diags).lower()

    if "missing \\documentclass" in messages or "missing documentclass" in messages:
        if r"\documentclass" not in out:
            out = (
                r"\documentclass[11pt,letterpaper]{article}" + "\n"
                + r"\usepackage[margin=0.75in]{geometry}" + "\n"
                + out
            )

    if r"\begin{document}" not in out:
        if r"\documentclass" in out:
            parts = out.split("\n", 1)
            out = parts[0] + "\n" + r"\begin{document}" + "\n" + (parts[1] if len(parts) > 1 else "")
        else:
            out = r"\begin{document}" + "\n" + out

    if r"\end{document}" not in out:
        out = out.rstrip() + "\n" + r"\end{document}" + "\n"

    for env in ("itemize", "enumerate"):
        begins = len(re.findall(rf"\\begin\{{{env}\}}", out))
        ends = len(re.findall(rf"\\end\{{{env}\}}", out))
        if begins > ends:
            out = out.rstrip() + ("\n" + rf"\end{{{env}}}") * (begins - ends) + "\n"
        elif ends > begins and r"\begin{document}" in out:
            insert = ("\n" + rf"\begin{{{env}}}") * (ends - begins)
            out = out.replace(r"\begin{document}", r"\begin{document}" + insert, 1)

    return out


def generate_from_form(
    form: dict[str, Any] | None,
    *,
    title: str = "",
    use_llm: bool | None = None,  # kept for call-site compat; ignored — always deterministic
) -> GenerateResult:
    """Seed + repair loop. used_llm is always False (no live model path)."""
    _ = use_llm
    latex = form_to_latex(form, title=title)
    used_llm = False
    iterations = 1

    if not latex or r"\begin{document}" not in latex:
        return GenerateResult(
            latex="",
            used_llm=used_llm,
            iterations=iterations,
            error="seed produced empty LaTeX",
        )

    last_diags: list[dict[str, Any]] = []
    for _ in range(MAX_REPAIR):
        last_diags = lint_latex(latex, track="latex")
        errors = [d for d in last_diags if d.get("severity") == "error"]
        if not errors:
            break
        repaired = _repair_latex(latex, errors)
        iterations += 1
        if repaired == latex:
            break
        latex = repaired

    last_diags = lint_latex(latex, track="latex")
    if not latex.strip() or r"\begin{document}" not in latex:
        return GenerateResult(
            latex=latex,
            used_llm=used_llm,
            iterations=iterations,
            diagnostics=last_diags,
            error="generate failed structural checks",
        )

    return GenerateResult(
        latex=latex,
        used_llm=used_llm,
        iterations=iterations,
        diagnostics=last_diags,
    )

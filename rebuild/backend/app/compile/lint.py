"""Lightweight LaTeX diagnostics with short fix suggestions (rule-based)."""

from __future__ import annotations

import re
from typing import Any


def lint_latex(source: str, *, track: str = "latex") -> list[dict[str, Any]]:
    """
    Lint LaTeX source for LATEX_ONLY path.
    Structured/FORM_PATH: lint is product-hidden; empty source is not an error.
    """
    text = source or ""
    lines = text.splitlines()
    diags: list[dict[str, Any]] = []

    def add(
        severity: str,
        message: str,
        line: int | None = None,
        *,
        suggestion: str | None = None,
    ) -> None:
        d: dict[str, Any] = {"severity": severity, "message": message}
        if line is not None:
            d["line"] = line
        if suggestion:
            d["suggestion"] = suggestion
            # Keep message scannable: append short fix when not already in message
            if suggestion not in message:
                d["message"] = f"{message} — fix: {suggestion}"
        diags.append(d)

    if not text.strip():
        if (track or "").strip().lower() != "latex":
            return []
        add("error", "Source is empty", 1, suggestion="Add a full document skeleton")
        return diags

    if not re.search(r"\\documentclass\b", text):
        add(
            "error",
            r"Missing \documentclass",
            1,
            suggestion=r"Add \documentclass[11pt]{article} at the top",
        )

    begin_doc = re.search(r"\\begin\{document\}", text)
    end_doc = re.search(r"\\end\{document\}", text)
    if not begin_doc:
        add(
            "error",
            r"Missing \begin{document}",
            _find_line(lines, r"\\documentclass") or 1,
            suggestion=r"Add \begin{document} after the preamble",
        )
    if not end_doc:
        add(
            "error",
            r"Missing \end{document}",
            len(lines) or 1,
            suggestion=r"Add \end{document} at the end of the file",
        )
    if begin_doc and end_doc and begin_doc.start() > end_doc.start():
        add(
            "error",
            r"\end{document} appears before \begin{document}",
            1,
            suggestion="Move \\begin{document} above \\end{document}",
        )

    # unmatched braces (rough)
    depth = 0
    for i, line in enumerate(lines, start=1):
        code = re.sub(r"%.*$", "", line)
        for ch in code:
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth < 0:
                    add(
                        "error",
                        "Unmatched closing brace",
                        i,
                        suggestion="Remove an extra } or add a matching {",
                    )
                    depth = 0
                    break
    if depth > 0:
        add(
            "warning",
            f"Unmatched opening brace(s): {depth}",
            len(lines) or 1,
            suggestion="Add missing } to close each {",
        )

    # begin/end env balance (common envs)
    for env in ("itemize", "enumerate", "center", "tabular", "minipage"):
        begins = len(re.findall(rf"\\begin\{{{env}\}}", text))
        ends = len(re.findall(rf"\\end\{{{env}\}}", text))
        if begins != ends:
            more_begin = begins > ends
            add(
                "error",
                f"Environment {env}: {begins} begin vs {ends} end",
                _find_line(lines, rf"\\begin\{{{env}\}}") or 1,
                suggestion=(
                    rf"Add \end{{{env}}}"
                    if more_begin
                    else rf"Remove extra \end{{{env}}} or add \begin{{{env}}}"
                ),
            )

    # unescaped special chars outside comments (common resume footgun)
    for i, line in enumerate(lines, start=1):
        code = re.sub(r"%.*$", "", line)
        # skip command names; look for bare & % $ # outside math-ish
        if re.search(r"(?<!\\)&", code):
            add(
                "warning",
                "Bare & character",
                i,
                suggestion=r"Use \& for a literal ampersand",
            )
            break

    # common typo
    if re.search(r"\\begindocument\b", text) and not begin_doc:
        add(
            "error",
            r"Found \begindocument (missing braces)",
            _find_line(lines, r"\\begindocument") or 1,
            suggestion=r"Use \begin{document}",
        )

    return diags


def _find_line(lines: list[str], pattern: str) -> int | None:
    cre = re.compile(pattern)
    for i, line in enumerate(lines, start=1):
        if cre.search(line):
            return i
    return None

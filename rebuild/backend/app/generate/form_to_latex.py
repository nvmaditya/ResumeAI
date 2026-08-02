"""Deterministic form→LaTeX seed (template fallback / first draft).

Skill-aligned (resume-latex-generate): full document, escape user text,
never invent facts, skip empty sections. Uses product form shape
(experience.company, education.degree, etc.). Honors form section_order.
"""

from __future__ import annotations

from typing import Any

DEFAULT_SECTION_ORDER = ("experience", "education", "projects", "skills")


def _esc(s: Any) -> str:
    t = str(s or "")
    out: list[str] = []
    for ch in t:
        if ch in "\\&%$#_{}":
            out.append("\\" + ch)
        elif ch == "~":
            out.append(r"\textasciitilde{}")
        elif ch == "^":
            out.append(r"\textasciicircum{}")
        else:
            out.append(ch)
    return "".join(out)


def _basics(data: dict[str, Any]) -> dict[str, str]:
    b = data.get("basics") if isinstance(data.get("basics"), dict) else {}
    b = b or {}
    return {
        "name": str(b.get("name") or "").strip(),
        "email": str(b.get("email") or "").strip(),
        "phone": str(b.get("phone") or "").strip(),
        "location": str(b.get("location") or "").strip(),
        "website": str(b.get("website") or b.get("portfolio") or "").strip(),
        "linkedin": str(b.get("linkedin") or "").strip(),
        "github": str(b.get("github") or "").strip(),
        "summary": str(b.get("summary") or "").strip(),
    }


def _has_rows(rows: Any) -> bool:
    if not isinstance(rows, list) or not rows:
        return False
    for r in rows:
        if isinstance(r, dict) and any(
            str(v or "").strip()
            for v in r.values()
            if not isinstance(v, (list, dict))
        ):
            return True
        if isinstance(r, dict):
            for v in r.values():
                if isinstance(v, list) and any(str(x or "").strip() for x in v):
                    return True
                if isinstance(v, str) and v.strip():
                    return True
    return False


def _bullets(text: Any) -> list[str]:
    raw = str(text or "").strip()
    if not raw:
        return []
    lines = [ln.strip() for ln in raw.replace("\r\n", "\n").split("\n")]
    return [ln.lstrip("•-* ").strip() for ln in lines if ln.strip()]


def _section_order(data: dict[str, Any]) -> list[str]:
    raw = data.get("section_order") or data.get("sectionOrder")
    allowed = set(DEFAULT_SECTION_ORDER)
    out: list[str] = []
    if isinstance(raw, list):
        for x in raw:
            k = str(x or "").strip().lower()
            if k == "work":
                k = "experience"
            if k in allowed and k not in out:
                out.append(k)
    for k in DEFAULT_SECTION_ORDER:
        if k not in out:
            out.append(k)
    return out


def _emit_experience(data: dict[str, Any]) -> list[str]:
    work = data.get("experience") or data.get("work") or []
    if not _has_rows(work):
        return []
    lines = [r"\section*{Experience}"]
    for w in work:
        if not isinstance(w, dict):
            continue
        role = _esc(w.get("position") or "Role")
        co = _esc(w.get("company") or w.get("name") or "")
        dates = _esc(str(w.get("dates") or "").strip())
        if not dates:
            dates = _esc(
                " -- ".join(
                    x
                    for x in [
                        str(w.get("startDate") or "").strip(),
                        str(w.get("endDate") or "").strip(),
                    ]
                    if x
                )
            )
        lines.append(rf"\textbf{{{role}}} \hfill {dates}\\")
        if co:
            lines.append(rf"\textit{{{co}}}\\")
        bullets = _bullets(w.get("summary"))
        if bullets:
            lines.append(r"\begin{itemize}")
            for bl in bullets:
                lines.append(rf"  \item {_esc(bl)}")
            lines.append(r"\end{itemize}")
        lines.append("")
    return lines


def _emit_education(data: dict[str, Any]) -> list[str]:
    edu = data.get("education") or []
    if not _has_rows(edu):
        return []
    lines = [r"\section*{Education}"]
    for e in edu:
        if not isinstance(e, dict):
            continue
        deg = " ".join(
            x
            for x in [
                _esc(e.get("degree") or e.get("studyType") or ""),
                _esc(e.get("area") or ""),
            ]
            if x
        ) or "Education"
        inst = _esc(e.get("institution") or "")
        dates = _esc(str(e.get("dates") or "").strip())
        lines.append(rf"\textbf{{{deg}}} \hfill {dates}\\")
        if inst:
            lines.append(rf"{inst}\\")
        lines.append("")
    return lines


def _emit_projects(data: dict[str, Any]) -> list[str]:
    projects = data.get("projects") or []
    if not _has_rows(projects):
        return []
    lines = [r"\section*{Projects}"]
    for p in projects:
        if not isinstance(p, dict):
            continue
        pn = _esc(p.get("name") or "Project")
        lines.append(rf"\textbf{{{pn}}}\\")
        if p.get("description"):
            lines.append(_esc(p.get("description")) + r"\\")
        if p.get("url"):
            u = str(p.get("url"))
            url = u if u.startswith("http") else f"https://{u}"
            lines.append(rf"\href{{{_esc(url)}}}{{{_esc(u)}}}\\")
        hl = p.get("highlights")
        bullets: list[str] = []
        if isinstance(hl, list):
            bullets = [str(x).strip() for x in hl if str(x).strip()]
        elif isinstance(hl, str):
            bullets = _bullets(hl)
        if bullets:
            lines.append(r"\begin{itemize}")
            for bl in bullets:
                lines.append(rf"  \item {_esc(bl)}")
            lines.append(r"\end{itemize}")
        lines.append("")
    return lines


def _emit_skills(data: dict[str, Any]) -> list[str]:
    skills = data.get("skills") or []
    if not _has_rows(skills):
        return []
    lines = [r"\section*{Skills}", r"\begin{itemize}"]
    for s in skills:
        if not isinstance(s, dict):
            continue
        kw = s.get("keywords")
        if isinstance(kw, list):
            kw = ", ".join(str(k) for k in kw)
        label = _esc(s.get("name") or "Skills")
        lines.append(rf"  \item \textbf{{{label}:}} {_esc(kw or '')}")
    lines.append(r"\end{itemize}")
    lines.append("")
    return lines


_SECTION_EMITTERS = {
    "experience": _emit_experience,
    "education": _emit_education,
    "projects": _emit_projects,
    "skills": _emit_skills,
}


def form_to_latex(data: dict[str, Any] | None, *, title: str = "") -> str:
    """Skill-aligned deterministic draft — no invented facts."""
    data = data or {}
    b = _basics(data)
    name = _esc(b["name"] or title or "Resume")
    lines: list[str] = [
        r"\documentclass[11pt,letterpaper]{article}",
        r"\usepackage[margin=0.75in]{geometry}",
        r"\usepackage[T1]{fontenc}",
        r"\usepackage{lmodern}",
        r"\usepackage[colorlinks=true,urlcolor=blue,linkcolor=blue,citecolor=blue,pdfborder={0 0 0}]{hyperref}",
        r"\usepackage{enumitem}",
        r"\setlist{nosep,leftmargin=*}",
        r"\pagestyle{empty}",
        r"\begin{document}",
        r"\begin{center}",
        rf"{{\Large\bfseries {name}}}\\[0.35em]",
    ]
    contact: list[str] = []
    if b["location"]:
        contact.append(_esc(b["location"]))
    if b["phone"]:
        contact.append(_esc(b["phone"]))
    if b["email"]:
        contact.append(rf"\href{{mailto:{_esc(b['email'])}}}{{{_esc(b['email'])}}}")
    if b["linkedin"]:
        url = (
            b["linkedin"]
            if b["linkedin"].startswith("http")
            else f"https://{b['linkedin']}"
        )
        contact.append(rf"\href{{{_esc(url)}}}{{LinkedIn}}")
    if b["github"]:
        url = (
            b["github"]
            if b["github"].startswith("http")
            else f"https://github.com/{b['github']}"
        )
        contact.append(rf"\href{{{_esc(url)}}}{{GitHub}}")
    if b["website"]:
        url = (
            b["website"]
            if b["website"].startswith("http")
            else f"https://{b['website']}"
        )
        contact.append(rf"\href{{{_esc(url)}}}{{Portfolio}}")
    if contact:
        lines.append(r"\small " + r" $|$ ".join(contact))
    lines.append(r"\end{center}")
    lines.append("")

    if b["summary"]:
        lines += [r"\section*{Summary}", _esc(b["summary"]), ""]

    for key in _section_order(data):
        emit = _SECTION_EMITTERS.get(key)
        if emit:
            lines.extend(emit(data))

    lines.append(r"\end{document}")
    lines.append("")
    return "\n".join(lines)

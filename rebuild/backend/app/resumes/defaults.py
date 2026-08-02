"""Default payloads for create paths (product 02)."""

from __future__ import annotations

EMPTY_FORM: dict = {
    "basics": {
        "name": "",
        "email": "",
        "phone": "",
        "location": "",
        "summary": "",
        "links": [],
    },
    "experience": [],
    "education": [],
    "projects": [],
    "skills": [],
}

STARTER_LATEX = r"""\documentclass[11pt]{article}
\usepackage[margin=1in]{geometry}
\begin{document}
\section*{Your Name}
% Starter LaTeX resume — edit freely
\begin{itemize}
  \item Role or highlight
\end{itemize}
\end{document}
"""

DEFAULT_AI_TITLE = "Untitled resume"  # create kind "ai" = form path (New resume)
DEFAULT_LATEX_TITLE = "LaTeX resume"

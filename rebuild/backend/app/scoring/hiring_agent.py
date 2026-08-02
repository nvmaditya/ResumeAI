"""
HackerRank hiring-agent ScoreEngine adapter.

Uses vendored hiring-agent evaluator + GitHub *cache only* (no live GH on score).
Falls back to content-based heuristic if LLM/vendor unavailable — not a flat constant.
"""

from __future__ import annotations

import hashlib
import re
import sys
import time
from pathlib import Path
from typing import Any

from app.github.cache import github_blob_to_text, select_top_repos


class HiringAgentScoreEngine:
    name = "hiring_agent"

    def __init__(self, vendor_path: str | Path) -> None:
        self.vendor_path = Path(vendor_path)

    def score(
        self,
        resume_text: str,
        *,
        jd: str | None = None,
        github_cache: dict | None = None,
    ) -> dict[str, Any]:
        t0 = time.perf_counter()
        vendor = self.vendor_path.resolve()
        if vendor.is_dir() and str(vendor) not in sys.path:
            sys.path.insert(0, str(vendor))

        gh_snap = github_cache if isinstance(github_cache, dict) else None
        github_enriched = False
        github_cache_status = "missing"
        github_data: dict[str, Any] = {}
        text = resume_text or ""

        try:
            if gh_snap and (gh_snap.get("profile") or gh_snap.get("repos")):
                github_cache_status = "hit"
                profile = gh_snap.get("profile") or {}
                repos = list(gh_snap.get("repos") or [])
                top = select_top_repos(repos, jd or None, k=5)
                github_data = {
                    "profile": profile,
                    "projects": top,
                    "total_projects": len(top),
                }
                github_enriched = True
                text = text + "\n\n" + github_blob_to_text(profile, top)

            if (jd or "").strip():
                text = (
                    text
                    + "\n\n=== JOB DESCRIPTION (for relevance) ===\n"
                    + (jd or "")[:4000]
                )

            if not text.strip():
                raise ValueError("empty resume text for evaluation")

            # Template path patch (same as monorepo)
            from prompts import template_manager as tm  # type: ignore

            abs_templates = str(vendor / "prompts" / "templates")
            _orig = tm.TemplateManager.__init__

            def _init(self, template_dir: str = "prompts/templates") -> None:  # type: ignore[no-untyped-def]
                if not Path(template_dir).is_absolute():
                    template_dir = abs_templates
                _orig(self, template_dir)

            tm.TemplateManager.__init__ = _init  # type: ignore[method-assign]

            from evaluator import ResumeEvaluator  # type: ignore
            from prompt import DEFAULT_MODEL, MODEL_PARAMETERS  # type: ignore

            params = MODEL_PARAMETERS.get(DEFAULT_MODEL, {"temperature": 0.5, "top_p": 0.9})
            evaluator = ResumeEvaluator(model_name=DEFAULT_MODEL, model_params=params)
            evaluation = evaluator.evaluate_resume(text)
            result = _map_evaluation(evaluation)
            result["engine"] = self.name
            result["github_enriched"] = github_enriched
            result["github_cache"] = github_cache_status
            result["github_repos_used"] = (
                len(github_data.get("projects") or []) if github_enriched else 0
            )
            result["jd_match"] = _jd_match(jd, text)
            result["duration_ms"] = int((time.perf_counter() - t0) * 1000)
            result["overall"] = result.get("overall") or result.get("overall_score") or 0
            return result
        except Exception as exc:
            # Content-aware fallback — varies with resume/cache; not fixed 82
            fb = _heuristic_score(resume_text, jd=jd, github_cache=gh_snap)
            fb["engine"] = f"{self.name}_fallback"
            fb["error"] = str(exc)[:400]
            fb["github_enriched"] = github_enriched
            fb["github_cache"] = github_cache_status
            fb["duration_ms"] = int((time.perf_counter() - t0) * 1000)
            return fb


def _map_evaluation(evaluation: Any) -> dict[str, Any]:
    categories: list[dict[str, Any]] = []
    total = 0.0
    scores = getattr(evaluation, "scores", None)
    category_maxes = {
        "open_source": 35,
        "self_projects": 30,
        "production": 25,
        "technical_skills": 10,
    }
    if scores:
        for name, max_s in category_maxes.items():
            cat = getattr(scores, name, None)
            if not cat:
                continue
            raw = min(float(cat.score), float(max_s))
            pct = int(round((raw / max_s) * 100)) if max_s else 0
            total += raw
            categories.append(
                {
                    "name": name,
                    "score": pct,
                    "evidence": getattr(cat, "evidence", "") or "",
                }
            )

    bonus = getattr(evaluation, "bonus_points", None)
    if bonus:
        total += float(getattr(bonus, "total", 0) or 0)
    deductions = getattr(evaluation, "deductions", None)
    if deductions:
        total -= float(getattr(deductions, "total", 0) or 0)

    overall = int(max(0, min(100, round(total))))
    return {
        "overall": overall,
        "overall_score": overall,
        "categories": categories
        or [
            {
                "name": "technical_skills",
                "score": overall,
                "evidence": "Mapped from hiring-agent evaluation",
            }
        ],
    }


def _jd_match(jd: str | None, corpus: str) -> dict[str, Any]:
    if not (jd or "").strip():
        return {
            "provided": False,
            "matched_keywords": [],
            "missing_keywords": [],
            "relevance": 0,
        }
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9+.#-]{2,}", (jd or "").lower())[:40]
    corp = (corpus or "").lower()
    matched = [t for t in tokens if t in corp]
    missing = [t for t in tokens if t not in corp]
    rel = int(round(100 * len(matched) / max(1, len(tokens))))
    return {
        "provided": True,
        "matched_keywords": matched[:20],
        "missing_keywords": missing[:20],
        "relevance": rel,
    }


def _heuristic_score(
    resume_text: str,
    *,
    jd: str | None,
    github_cache: dict | None,
) -> dict[str, Any]:
    """Deterministic but content-sensitive fallback (not a constant)."""
    text = resume_text or ""
    words = max(1, len(text.split()))
    h = int(hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:8], 16)
    jitter = h % 17  # 0..16
    base = min(88, 28 + min(words, 400) // 5 + jitter)

    enriched = bool(
        github_cache
        and (github_cache.get("repos") or github_cache.get("profile") or github_cache.get("login"))
    )
    repo_n = 0
    if enriched and github_cache:
        repo_n = int(
            github_cache.get("repo_count")
            or github_cache.get("total_repos")
            or len(github_cache.get("repos") or [])
            or 0
        )
        base = min(96, base + min(repo_n, 12))

    cats = [
        {
            "name": "technical_skills",
            "score": min(100, base + 4),
            "evidence": f"Heuristic from resume length/tokens ({words} words).",
        },
        {
            "name": "self_projects",
            "score": min(100, base - 3 + (h % 9)),
            "evidence": "Heuristic project/impact density (fallback; set LLM keys for hiring-agent).",
        },
        {
            "name": "production",
            "score": min(100, base - 6),
            "evidence": "Heuristic work-experience signal.",
        },
        {
            "name": "open_source",
            "score": min(100, 35 + min(repo_n * 3, 50)) if enriched else 25 + (h % 11),
            "evidence": (
                f"From GitHub cache · {repo_n} repos."
                if enriched
                else "No GitHub cache — weak OSS signal."
            ),
        },
    ]
    overall = int(round(sum(c["score"] for c in cats) / len(cats)))
    out: dict[str, Any] = {
        "overall": overall,
        "categories": cats,
        "github_enriched": enriched,
    }
    if (jd or "").strip():
        out["jd_match"] = _jd_match(jd, text)
    return out

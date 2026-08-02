"""Deterministic content-sensitive stub ScoreEngine — no flat constant score."""

from __future__ import annotations

from typing import Any

from app.scoring.hiring_agent import _heuristic_score


class StubScoreEngine:
    name = "stub"

    def score(
        self,
        resume_text: str,
        *,
        jd: str | None = None,
        github_cache: dict | None = None,
    ) -> dict[str, Any]:
        out = _heuristic_score(resume_text, jd=jd, github_cache=github_cache)
        out["engine"] = self.name
        return out


def build_score_engine(backend: str | None = None, vendor_path: str | None = None):
    b = (backend or "stub").strip().lower()
    if b in ("hiring_agent", "hiring-agent", "ha"):
        from app.scoring.hiring_agent import HiringAgentScoreEngine

        if not vendor_path:
            raise ValueError("hiring_agent_path required for hiring_agent backend")
        return HiringAgentScoreEngine(vendor_path)
    return StubScoreEngine()

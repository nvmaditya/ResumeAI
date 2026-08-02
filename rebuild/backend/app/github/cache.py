"""
GitHub snapshot for scoring — same contract as monorepo app.github.cache.

Network only on explicit Settings → Update GitHub data.
Score path must only *read* the stored snapshot.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def format_cache_status(
    *,
    username: str,
    cache: dict[str, Any] | None,
    updated_at: str | None,
) -> str:
    if not cache:
        return "No GitHub cache yet — Update GitHub data in Settings."
    login = (
        cache.get("username")
        or cache.get("login")
        or (cache.get("profile") or {}).get("username")
        or username
        or "user"
    )
    n = int(
        cache.get("total_repos")
        or cache.get("repo_count")
        or len(cache.get("repos") or [])
        or 0
    )
    when = updated_at or cache.get("fetched_at") or "unknown time"
    return f"Cached @{login} · {n} repos · {when}"


def load_cache_from_settings_shape(cache: dict[str, Any] | None) -> dict[str, Any] | None:
    """Normalize stored JSON for score engine."""
    if not isinstance(cache, dict) or not cache:
        return None
    return cache


def refresh_github(username: str, *, vendor_path: str) -> dict[str, Any]:
    """
    Fetch profile + repos via HackerRank hiring-agent vendor helpers.
    Stores lean snapshot; no LLM. Fails clearly if profile missing / network error.
    """
    username = (username or "").strip().lstrip("@")
    if not username:
        raise ValueError("github_username required")

    vendor = Path(vendor_path).resolve()
    if not vendor.is_dir():
        raise ValueError(f"hiring-agent vendor not found: {vendor}")
    if str(vendor) not in sys.path:
        sys.path.insert(0, str(vendor))

    try:
        from github import (  # type: ignore
            extract_github_username,
            fetch_all_github_repos,
            fetch_github_profile,
            generate_profile_json,
        )
    except ImportError as exc:
        raise ValueError(
            "hiring-agent github module unavailable (install vendor deps: requests)"
        ) from exc

    url = f"https://github.com/{username}"
    extracted = extract_github_username(url) or extract_github_username(username)
    if extracted:
        username = extracted
        url = f"https://github.com/{username}"

    profile = fetch_github_profile(url)
    if not profile:
        raise ValueError(f"GitHub profile not found: {username}")

    repos_raw = fetch_all_github_repos(url) or []
    repos: list[dict[str, Any]] = []
    for p in repos_raw:
        if not isinstance(p, dict):
            continue
        repos.append(
            {
                "name": p.get("name"),
                "description": p.get("description"),
                "github_url": p.get("github_url") or p.get("html_url"),
                "live_url": p.get("live_url") or p.get("homepage"),
                "technologies": p.get("technologies") or p.get("language") or [],
                "project_type": p.get("project_type") or "self_project",
                "contributor_count": p.get("contributor_count") or 1,
                "author_commit_count": p.get("author_commit_count") or 0,
                "stars": (p.get("github_details") or {}).get("stars")
                or p.get("stargazers_count")
                or 0,
                "language": p.get("language")
                or (
                    (p.get("technologies") or [None])[0]
                    if isinstance(p.get("technologies"), list)
                    else p.get("technologies")
                ),
            }
        )

    snap = {
        "username": username,
        "login": username,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "profile": generate_profile_json(profile)
        if callable(generate_profile_json)
        else {"username": username},
        "repos": repos,
        "total_repos": len(repos),
        "repo_count": len(repos),
        "source": "github_api",
    }
    return snap


def select_top_repos(
    repos: list[dict[str, Any]],
    job_description: str | None,
    *,
    k: int = 5,
) -> list[dict[str, Any]]:
    if not repos:
        return []
    if not (job_description or "").strip():
        ranked = sorted(
            repos,
            key=lambda r: (
                int(r.get("stars") or 0),
                int(r.get("author_commit_count") or 0),
            ),
            reverse=True,
        )
        return ranked[:k]
    tokens = [
        t
        for t in __import__("re").findall(
            r"[a-zA-Z][a-zA-Z0-9+.#-]{1,}", (job_description or "").lower()
        )
        if len(t) > 2
    ]
    scored: list[tuple[float, dict[str, Any]]] = []
    for r in repos:
        blob = " ".join(
            str(x)
            for x in (
                r.get("name"),
                r.get("description"),
                r.get("language"),
                r.get("technologies"),
            )
            if x
        ).lower()
        hit = sum(1 for t in tokens if t in blob)
        score = hit * 10 + int(r.get("stars") or 0) * 0.1
        scored.append((score, r))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in scored[:k]]


def github_blob_to_text(profile: dict[str, Any] | None, projects: list[dict[str, Any]]) -> str:
    lines = ["=== GITHUB DATA ==="]
    if profile:
        lines.append(f"username: {profile.get('username') or profile.get('login')}")
        if profile.get("bio"):
            lines.append(f"bio: {profile.get('bio')}")
        if profile.get("public_repos") is not None:
            lines.append(f"public_repos: {profile.get('public_repos')}")
    lines.append("projects:")
    for p in projects:
        lines.append(
            f"- {p.get('name')}: {p.get('description') or ''} "
            f"stars={p.get('stars')} url={p.get('github_url') or ''}"
        )
    return "\n".join(lines)

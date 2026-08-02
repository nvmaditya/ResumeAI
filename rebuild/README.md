# ResumeAI — Product workspace

This directory is a **standalone product workspace** for implementing ResumeAI from the **current shipped product contract**. It is **not** the live monorepo `backend/` / `frontend/` application tree.

| Artifact | Purpose |
|----------|---------|
| [`PRD.md`](./PRD.md) | Detailed product requirements for the **shipped** product (product target) |
| [`AGENTS.md`](./AGENTS.md) | Rules for coding agents — **binding process**, product constraints, modular seams |
| [`PLAN.md`](./PLAN.md) | Phased implementation plan + phase → skill map |
| [`LESSONS.md`](./LESSONS.md) | Workspace memory: product-intent mistakes |
| [`STRUCTURE.md`](./STRUCTURE.md) | **Structure-only** IA / chrome inventory of the live product app (Playwright) |
| [`DESIGN.md`](./DESIGN.md) | **Presentation** design system (paper + ledger tokens, motion, quality bar); implements within STRUCTURE chrome; supersedes [`OLD-DESIGN.md`](./OLD-DESIGN.md) |
| [`docs/product/`](./docs/product/README.md) | Product bible (seeded from repo `docs/product-v2/`) |
| [`backend/`](./backend/) | FastAPI app — modular seams, health, **auth** + protected `/resumes` |
| [`frontend/`](./frontend/) | React + Vite + TS — login/register, session, protected home |
| [`tests/`](./tests/) | Process contract, health, seams, **auth hard rules** |

**Live app** remains at repo root (`backend/`, `frontend/`).  
**Canonical product-v2 docs** still live at [`docs/product-v2/`](../docs/product-v2/README.md).

## Run the app

### One command (recommended)

Requires **[uv](https://docs.astral.sh/uv/)** and Node/npm. From this workspace root:

```bash
./start.sh
# API only:
./start.sh --no-frontend
# custom ports:
API_PORT=8001 FE_PORT=5173 ./start.sh
```

`start.sh` runs `uv sync` in `backend/`, starts **uvicorn** via `uv run` on **:8001**, then **Vite** on **:5173** (proxies `/api` → API). Ctrl+C stops both.

Git Bash / WSL on Windows: `bash start.sh`

### Prerequisites

- **uv** (Python 3.12+ managed by uv; see `backend/pyproject.toml`)
- Node 20+ / npm for the frontend

### API only (port 8001 — avoid clashing with live monorepo :8000)

```bash
cd backend
uv sync --group dev
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

```powershell
# PowerShell equivalent
cd backend
uv sync --group dev
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

Health check: `http://127.0.0.1:8001/api/v1/health`  
Expect: `status=ok`, `service=resumeai`, seams list.

**Env:** Copy monorepo secrets into product backend (never commit):

```powershell
Copy-Item ..\backend\.env .\backend\.env
```

The API loads `backend/.env` on startup (keys already present in the process env win).  
`SCORE_BACKEND`, `TECTONIC_PATH` come from that file.

**Auth (Phase 1):**

| Method | Path | Notes |
|--------|------|--------|
| POST | `/api/v1/auth/register` | email + password ≥ 8 → **auto-login** bearer token |
| POST | `/api/v1/auth/login` | returns bearer token |
| POST | `/api/v1/auth/logout` | invalidates token |
| GET | `/api/v1/resumes` | **protected** list (`?q=` search, `?tags=` AND filter) |
| POST | `/api/v1/resumes` | `{ "create": "ai" \| "latex" }` — no template create |
| GET/PATCH/DELETE | `/api/v1/resumes/{id}` | get, title/tags patch, delete |

UI: `/register`, `/login`, `/` (list + **New resume** / **New LaTeX** only), `/resumes/:id` **workspace** (identity + File|Build|Score|Danger).

| Path | Editor | Compile | Lint | After compile |
|------|--------|---------|------|---------------|
| **New resume** (`structured`) | Form only | form → LaTeX snapshot + PDF | Hidden | Stay form; PDF stale until recompile |
| **New LaTeX** (`latex`) | Source only | source → PDF | Visible + fix hints | Stay source |

**Build APIs:** `POST .../compile` → `{ok, engine, size}` (structured stays structured); `POST .../lint` (latex); `GET .../pdf`; `GET .../tex` (last compile snapshot on form path).

**No AI Generate** in UI. Legacy `POST .../generate` does not flip track.

**Versions (Phase 6):** LaTeX checkpoints — not auto-on-save; unchanged commit is a no-op.

**Score + GitHub cache (Phase 7):** Manual only. Score uses **Settings cache only** (no live GitHub on score). Default engine: **hiring_agent** (HackerRank vendor at monorepo `backend/vendor/hiring-agent`); falls back to content-heuristic if LLM unavailable.

| Method | Path | Notes |
|--------|------|--------|
| GET/PATCH | `/api/v1/settings` | github_username + cache_status |
| POST | `/api/v1/settings/github/update` | live fetch via hiring-agent `github.py` once; store snapshot (stub if network fails) |
| POST | `/api/v1/resumes/{id}/score` | start job `{job_id, status}` optional `{jd}` |
| GET | `/api/v1/jobs/{job_id}` | poll queued→processing→complete\|failed + result |

**Compile:** Prefer monorepo `backend/bin/tectonic.exe` or `TECTONIC_PATH`. Complex LaTeX no longer silent-falls back to layout garbage PDF — errors surface instead.

UI: **Settings** drawer; **Check score** / **Re-check score** + stepper; LaTeX editor with line numbers + token colors.

| Method | Path | Notes |
|--------|------|--------|
| GET | `/api/v1/resumes/{id}/versions` | list newest-first (message + time) |
| POST | `/api/v1/resumes/{id}/versions` | `{ "message"? }` → commit; or `{committed:false, unchanged:true}` |
| POST | `/api/v1/resumes/{id}/versions/{vid}/restore` | replace live `latex_source` only; quiet recompile |
| DELETE | `/api/v1/resumes/{id}/versions/{vid}` | delete checkpoint only |

### Frontend only (port 5173; proxies `/api` → :8001)

```bash
cd frontend
npm install
npm run dev
npm run build   # production build
```

### Tests (from this workspace root)

```bash
cd backend && uv sync --group dev && cd ..
uv run --project backend pytest tests/ -q
# includes test_process_contract.py, test_health.py, test_seams.py
# Run twice before claiming a phase done (skills-guide: no early stop)
```

## Start here (process = skills-guide)

**How to work** is not optional: follow **`C:\Code\skills-guide`** (`HOW_TO_WORK.md` + `SKILLS_GUIDE.md`) and this workspace’s phase map in [`PLAN.md`](./PLAN.md) / [`AGENTS.md`](./AGENTS.md).

1. Read **[PRD.md](./PRD.md)** for scope, journeys, constraints.  
2. Use **[docs/product/](./docs/product/README.md)** for feature behavior.  
3. Follow **[PLAN.md](./PLAN.md)** phase by phase (skills per phase).  
4. Agents: **[AGENTS.md](./AGENTS.md)** — binding process: **test-driven-development**, multi-pass verification (**no early stopping**), **ponytail**, modular seams, **dispatching-parallel-agents** only for independent tracks, **high-end-visual-design** only after chrome works.  
5. **Skills (general):** `C:\Code\skills-guide` — do not fork into this tree. Phase skill map stays in `PLAN.md`.  
6. **Memory:** [`LESSONS.md`](./LESSONS.md); progress in `PLAN.md`; global prefs `~/.grok/memory/MEMORY.md`.

## Process contract (summary)

| Requirement | Detail |
|-------------|--------|
| Process SoT | `C:\Code\skills-guide` + AGENTS binding section |
| Loop | Think → Plan → Implement (small) → Verify → Review |
| Hard rules | **test-driven-development** + **ponytail** |
| Done gate | Multi-pass verify — **not** one unit test alone |
| Parallel | **dispatching-parallel-agents** only for independent tracks |
| UI | Structure first; **high-end-visual-design** after chrome works |
| Seams | auth, compile, score, jobs |

## Layout

```
.
  backend/app/          ← create_app, health, seam packages
    auth/ compile/ scoring/ jobs/
  frontend/             ← Vite React shell
  tests/                ← process + health + seams
  docs/product/         ← product bible copy
  AGENTS.md PLAN.md PRD.md LESSONS.md
  start.sh              ← uv + API + frontend
```

## Relationship to monorepo

```
ResumeAI/
  backend/  frontend/     ← live product (do not treat as this workspace)
  docs/product-v2/        ← source product bible
  <this workspace>/       ← product app scaffold (not the live tree)
```

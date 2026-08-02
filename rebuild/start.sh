#!/usr/bin/env bash
# Start ResumeAI: API (uv + uvicorn) + frontend (Vite).
# Usage (from this workspace root):
#   ./start.sh
#   API_PORT=8001 FE_PORT=5173 ./start.sh
#   ./start.sh --no-frontend
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_PORT="${API_PORT:-8001}"
FE_PORT="${FE_PORT:-5173}"
API_HOST="${API_HOST:-127.0.0.1}"
WITH_FRONTEND=1

for arg in "$@"; do
  case "$arg" in
    --no-frontend) WITH_FRONTEND=0 ;;
    -h|--help)
      cat <<EOF
Start ResumeAI dev servers (uv-managed API + Vite frontend).

  ./start.sh              API :${API_PORT} + frontend :${FE_PORT}
  ./start.sh --no-frontend
  API_PORT=8001 FE_PORT=5173 ./start.sh

Requires: uv, Node/npm (for frontend)
EOF
      exit 0
      ;;
    *)
      echo "Unknown option: $arg (try --help)" >&2
      exit 2
      ;;
  esac
done

# Git Bash on Windows often lacks ~/.local/bin on PATH
if ! command -v uv >/dev/null 2>&1; then
  for candidate in \
    "${HOME}/.local/bin/uv" \
    "${HOME}/.local/bin/uv.exe" \
    "/c/Users/${USER}/.local/bin/uv.exe" \
    "${LOCALAPPDATA}/Programs/uv/uv.exe"
  do
    if [[ -n "${candidate}" && -x "${candidate}" ]]; then
      PATH="$(dirname "${candidate}"):${PATH}"
      export PATH
      break
    fi
  done
fi
if ! command -v uv >/dev/null 2>&1; then
  echo "error: uv not found. Install: https://docs.astral.sh/uv/  (ensure uv is on PATH)" >&2
  exit 1
fi

API_PID=""
FE_PID=""

cleanup() {
  local code=$?
  set +e
  if [[ -n "${FE_PID}" ]] && kill -0 "${FE_PID}" 2>/dev/null; then
    kill "${FE_PID}" 2>/dev/null || true
    wait "${FE_PID}" 2>/dev/null || true
  fi
  if [[ -n "${API_PID}" ]] && kill -0 "${API_PID}" 2>/dev/null; then
    kill "${API_PID}" 2>/dev/null || true
    wait "${API_PID}" 2>/dev/null || true
  fi
  exit "${code}"
}
trap cleanup EXIT INT TERM

echo "==> Syncing backend deps with uv"
cd "${ROOT}/backend"
uv sync --group dev

echo "==> Starting API on http://${API_HOST}:${API_PORT} (uv run uvicorn)"
# backend/ is package root (app.main)
uv run uvicorn app.main:app --reload --host "${API_HOST}" --port "${API_PORT}" &
API_PID=$!

echo "==> Waiting for health"
health_url="http://${API_HOST}:${API_PORT}/api/v1/health"
for i in $(seq 1 40); do
  if command -v curl >/dev/null 2>&1; then
    if curl -sf "${health_url}" >/dev/null 2>&1; then
      echo "    health ok: ${health_url}"
      if command -v curl >/dev/null 2>&1; then
        curl -s "${health_url}" || true
        echo
      fi
      break
    fi
  else
    # no curl: brief wait then continue
    if [[ "$i" -eq 10 ]]; then
      echo "    (curl not found; assuming API starting)"
      break
    fi
  fi
  if ! kill -0 "${API_PID}" 2>/dev/null; then
    echo "error: API process exited early" >&2
    exit 1
  fi
  sleep 0.25
  if [[ "$i" -eq 40 ]]; then
    echo "error: health check timed out at ${health_url}" >&2
    exit 1
  fi
done

if [[ "${WITH_FRONTEND}" -eq 1 ]]; then
  if ! command -v npm >/dev/null 2>&1; then
    echo "error: npm not found (install Node or use --no-frontend)" >&2
    exit 1
  fi
  echo "==> Frontend deps"
  cd "${ROOT}/frontend"
  if [[ ! -d node_modules ]]; then
    npm install
  fi
  echo "==> Starting Vite on http://${API_HOST}:${FE_PORT} (proxy /api → :${API_PORT})"
  npm run dev -- --host "${API_HOST}" --port "${FE_PORT}" &
  FE_PID=$!
fi

echo
echo "ResumeAI is up."
echo "  API:      http://${API_HOST}:${API_PORT}/api/v1/health"
if [[ "${WITH_FRONTEND}" -eq 1 ]]; then
  echo "  Frontend: http://${API_HOST}:${FE_PORT}/"
fi
echo "Ctrl+C to stop."
echo

# Prefer waiting on frontend (interactive); else API only
if [[ -n "${FE_PID}" ]]; then
  wait "${FE_PID}"
else
  wait "${API_PID}"
fi

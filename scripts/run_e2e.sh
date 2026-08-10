#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_NAME="chooseyourtube-e2e"
export BACKEND_HOST_PORT="${E2E_BACKEND_HOST_PORT:-8002}"
export FRONTEND_HOST_PORT="${E2E_FRONTEND_HOST_PORT:-5175}"
export API_ORIGIN="http://127.0.0.1:${FRONTEND_HOST_PORT}"
export API_CORS_ORIGINS="$API_ORIGIN"
export SMOKE_API_URL="http://127.0.0.1:${BACKEND_HOST_PORT}"
export FULL_E2E_API_URL="$SMOKE_API_URL"
export FULL_E2E_BASE_URL="$API_ORIGIN"
COMPOSE=(docker compose -p "$PROJECT_NAME" -f "$ROOT_DIR/compose.yaml" -f "$ROOT_DIR/docker-compose.e2e.yml" --env-file "$ROOT_DIR/.env.example")

cleanup() {
  "${COMPOSE[@]}" down --volumes --remove-orphans
}
trap cleanup EXIT

cleanup
"${COMPOSE[@]}" up -d --build postgres redis migrate
"${COMPOSE[@]}" run --rm --build seed-e2e
"${COMPOSE[@]}" up -d --build backend worker frontend
python3 "$ROOT_DIR/scripts/compose_smoke.py"

cd "$ROOT_DIR/frontend"
pnpm exec playwright test --config playwright.full.config.ts

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_NAME="chooseyourtube-e2e"
COMPOSE=(docker compose -p "$PROJECT_NAME" -f "$ROOT_DIR/compose.yaml" -f "$ROOT_DIR/docker-compose.e2e.yml" --env-file "$ROOT_DIR/.env.example")

cleanup() {
  "${COMPOSE[@]}" down --volumes --remove-orphans
}
trap cleanup EXIT

cleanup
"${COMPOSE[@]}" up -d --build postgres redis migrate
"${COMPOSE[@]}" run --rm seed-e2e
"${COMPOSE[@]}" up -d --build backend worker frontend
python3 "$ROOT_DIR/scripts/compose_smoke.py"

cd "$ROOT_DIR/frontend"
pnpm exec playwright test --config playwright.full.config.ts

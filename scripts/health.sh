#!/usr/bin/env sh
set -eu

ENV_FILE=${ENV_FILE:-.env}
docker compose --env-file "$ENV_FILE" ps
curl --fail --silent --show-error http://localhost:8000/health/live >/dev/null
curl --fail --silent --show-error http://localhost:8000/health/ready >/dev/null
curl --fail --silent --show-error http://localhost:5173/api/meta >/dev/null
docker compose --env-file "$ENV_FILE" exec -T redis redis-cli ping | grep -q PONG
docker compose --env-file "$ENV_FILE" exec -T redis redis-cli exists chooseyourtube:worker:heartbeat | grep -q 1
echo "ChooseYourTube is healthy."

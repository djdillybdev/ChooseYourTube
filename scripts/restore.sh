#!/usr/bin/env sh
set -eu

ENV_FILE=${ENV_FILE:-.env}

if [ "${CONFIRM:-}" != "RESTORE" ]; then
  echo "Restore is destructive. Re-run with CONFIRM=RESTORE BACKUP_FILE=path/to/file." >&2
  exit 1
fi
if [ -z "${BACKUP_FILE:-}" ] || [ ! -f "$BACKUP_FILE" ]; then
  echo "BACKUP_FILE must name an existing custom-format pg_dump." >&2
  exit 1
fi

docker compose --env-file "$ENV_FILE" stop frontend backend worker
docker compose --env-file "$ENV_FILE" exec -T postgres psql --username postgres --dbname postgres \
  --command "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'chooseyourtube' AND pid <> pg_backend_pid();"
docker compose --env-file "$ENV_FILE" exec -T postgres dropdb --username postgres --if-exists chooseyourtube
docker compose --env-file "$ENV_FILE" exec -T postgres createdb --username postgres chooseyourtube
docker compose --env-file "$ENV_FILE" exec -T postgres pg_restore --username postgres --dbname chooseyourtube --no-owner < "$BACKUP_FILE"
docker compose --env-file "$ENV_FILE" run --rm migrate
docker compose --env-file "$ENV_FILE" up -d backend worker frontend
./scripts/health.sh

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
docker compose --env-file "$ENV_FILE" exec -T postgres sh -c \
  'dropdb --username "$POSTGRES_USER" --force --if-exists "$POSTGRES_DB"'
docker compose --env-file "$ENV_FILE" exec -T postgres sh -c \
  'createdb --username "$POSTGRES_USER" "$POSTGRES_DB"'
docker compose --env-file "$ENV_FILE" exec -T postgres sh -c \
  'pg_restore --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --no-owner' < "$BACKUP_FILE"
docker compose --env-file "$ENV_FILE" run --rm migrate
docker compose --env-file "$ENV_FILE" up -d backend worker frontend
./scripts/health.sh

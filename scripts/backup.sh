#!/usr/bin/env sh
set -eu

ENV_FILE=${ENV_FILE:-.env}
mkdir -p backups
BACKUP_FILE=${BACKUP_FILE:-backups/chooseyourtube-$(date -u +%Y%m%dT%H%M%SZ).dump}

docker compose --env-file "$ENV_FILE" exec -T postgres \
  sh -c 'pg_dump --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --format custom' \
  > "$BACKUP_FILE"

echo "Database backup written to $BACKUP_FILE"

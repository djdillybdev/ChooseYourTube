#!/usr/bin/env sh
set -eu

ENV_FILE=${ENV_FILE:-.env}
mkdir -p backups
BACKUP_FILE=${BACKUP_FILE:-backups/chooseyourtube-$(date -u +%Y%m%dT%H%M%SZ).dump}

docker compose --env-file "$ENV_FILE" exec -T postgres \
  pg_dump --username postgres --dbname chooseyourtube --format custom > "$BACKUP_FILE"

echo "Database backup written to $BACKUP_FILE"

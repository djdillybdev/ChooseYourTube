#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
# shellcheck source=common.sh
. "$SCRIPT_DIR/common.sh"

require_root
load_env

[ "${CONFIRM:-}" = "RESTORE" ] \
  || die "Restore is destructive. Re-run with CONFIRM=RESTORE BACKUP_FILE=/absolute/path.dump."
[ -n "${BACKUP_FILE:-}" ] && [ "${BACKUP_FILE#/}" != "$BACKUP_FILE" ] && [ -f "$BACKUP_FILE" ] \
  || die "BACKUP_FILE must name an existing PostgreSQL custom-format dump."
compose exec -T postgres pg_restore --list < "$BACKUP_FILE" >/dev/null \
  || die "BACKUP_FILE is not a readable PostgreSQL custom-format dump."

compose stop caddy frontend backend worker
compose exec -T postgres sh -c \
  'dropdb --username "$POSTGRES_USER" --force --if-exists "$POSTGRES_DB"'
compose exec -T postgres sh -c \
  'createdb --username "$POSTGRES_USER" "$POSTGRES_DB"'
compose exec -T postgres sh -c \
  'pg_restore --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --no-owner' \
  < "$BACKUP_FILE"
compose run --rm migrate
compose up -d --wait backend worker frontend caddy
"$SCRIPT_DIR/health.sh"

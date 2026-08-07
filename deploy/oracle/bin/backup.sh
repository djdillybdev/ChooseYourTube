#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
# shellcheck source=common.sh
. "$SCRIPT_DIR/common.sh"

require_root
load_env

backup_dir=${BACKUP_DIR:-/var/backups/chooseyourtube}
[ "${backup_dir#/}" != "$backup_dir" ] && [ "$backup_dir" != "/" ] \
  || die "BACKUP_DIR must be a specific absolute directory."

umask 077
mkdir -p "$backup_dir"
backup_file="$backup_dir/chooseyourtube-$(date -u +%Y%m%dT%H%M%SZ).dump"
temporary_file="${backup_file}.tmp"
trap 'rm -f "$temporary_file"' EXIT HUP INT TERM

compose exec -T postgres sh -c \
  'pg_dump --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --format custom' \
  > "$temporary_file"
test -s "$temporary_file" || die "PostgreSQL produced an empty backup."
mv "$temporary_file" "$backup_file"
trap - EXIT HUP INT TERM

log "Database backup written to $backup_file."

#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
# shellcheck source=common.sh
. "$SCRIPT_DIR/common.sh"

require_root

[ -f "$ENV_FILE" ] || die "Missing $ENV_FILE. Copy deploy/oracle/oracle.env.example to .env and edit it first."
chmod 600 "$ENV_FILE"

auth_secret=$(awk -F= '$1 == "AUTH_SECRET" { sub(/^AUTH_SECRET=/, ""); print; exit }' "$ENV_FILE")
if [ -z "$auth_secret" ] \
  || [ "$auth_secret" = "replace-me" ] \
  || [ "$auth_secret" = "change-me-in-production-with-at-least-32-characters" ]; then
  replace_env_value AUTH_SECRET "$(openssl rand -hex 32)"
fi

postgres_password=$(awk -F= '$1 == "POSTGRES_PASSWORD" { sub(/^POSTGRES_PASSWORD=/, ""); print; exit }' "$ENV_FILE")
if [ -z "$postgres_password" ] || [ "$postgres_password" = "replace-me" ]; then
  replace_env_value POSTGRES_PASSWORD "$(openssl rand -hex 24)"
fi

log "Production secrets are prepared in $ENV_FILE."

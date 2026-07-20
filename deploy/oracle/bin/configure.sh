#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
# shellcheck source=common.sh
. "$SCRIPT_DIR/common.sh"

require_root

if [ ! -f "$ENV_FILE" ]; then
  cp "$REPO_DIR/deploy/oracle/oracle.env.example" "$ENV_FILE"
fi
chmod 600 "$ENV_FILE"

auth_secret=$(awk -F= '$1 == "AUTH_SECRET" { sub(/^AUTH_SECRET=/, ""); print; exit }' "$ENV_FILE")
if [ -z "$auth_secret" ] || [ "$auth_secret" = "replace-me" ]; then
  replace_env_value AUTH_SECRET "$(openssl rand -hex 32)"
fi

postgres_password=$(awk -F= '$1 == "POSTGRES_PASSWORD" { sub(/^POSTGRES_PASSWORD=/, ""); print; exit }' "$ENV_FILE")
if [ -z "$postgres_password" ] || [ "$postgres_password" = "replace-me" ]; then
  replace_env_value POSTGRES_PASSWORD "$(openssl rand -hex 24)"
fi

log "Production environment prepared at $ENV_FILE."
log "Edit its domain, email, release version, YouTube API key, and optional allowlist before deploying."

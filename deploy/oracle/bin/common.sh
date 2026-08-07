#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
REPO_DIR=$(CDPATH='' cd -- "$SCRIPT_DIR/../../.." && pwd)
ENV_FILE=${ENV_FILE:-$REPO_DIR/.env}

log() {
  printf '%s\n' "$*"
}

die() {
  printf 'Error: %s\n' "$*" >&2
  exit 1
}

require_root() {
  [ "$(id -u)" -eq 0 ] || die "Run this command as root."
}

load_env() {
  [ -f "$ENV_FILE" ] || die "Missing $ENV_FILE; run deploy/oracle/bin/configure.sh first."
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in
      ''|'#'*) continue ;;
    esac
    key=${line%%=*}
    value=${line#*=}
    [ "$line" != "$key" ] || die "Invalid line in $ENV_FILE: expected KEY=value."
    printf '%s' "$key" | grep -Eq '^[A-Z][A-Z0-9_]*$' \
      || die "Invalid environment key in $ENV_FILE: $key"
    case "$value" in
      *[!abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_./:@,%+=-]*)
        die "$key contains unsupported characters; do not quote values or include spaces."
        ;;
    esac
    export "$key=$value"
  done < "$ENV_FILE"
  COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME:-chooseyourtube}
  POSTGRES_USER=${POSTGRES_USER:-chooseyourtube}
  POSTGRES_DB=${POSTGRES_DB:-chooseyourtube}
  export COMPOSE_PROJECT_NAME POSTGRES_USER POSTGRES_DB
}

compose() {
  docker compose \
    --env-file "$ENV_FILE" \
    -f "$REPO_DIR/compose.yaml" \
    -f "$REPO_DIR/deploy/oracle/compose.yaml" \
    "$@"
}

replace_env_value() {
  key=$1
  value=$2
  temporary="${ENV_FILE}.tmp"
  awk -v key="$key" -v value="$value" '
    BEGIN { replaced = 0 }
    index($0, key "=") == 1 { print key "=" value; replaced = 1; next }
    { print }
    END { if (!replaced) print key "=" value }
  ' "$ENV_FILE" > "$temporary"
  chmod 600 "$temporary"
  mv "$temporary" "$ENV_FILE"
}

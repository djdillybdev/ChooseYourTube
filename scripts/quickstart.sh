#!/usr/bin/env sh
set -eu

ENV_FILE=${ENV_FILE:-.env}

if [ ! -f "$ENV_FILE" ]; then
  cp .env.example "$ENV_FILE"
fi

replace_env() {
  key=$1
  value=$2
  temporary="${ENV_FILE}.tmp"
  awk -v key="$key" -v value="$value" '
    BEGIN { replaced = 0 }
    index($0, key "=") == 1 { print key "=" value; replaced = 1; next }
    { print }
    END { if (!replaced) print key "=" value }
  ' "$ENV_FILE" > "$temporary"
  mv "$temporary" "$ENV_FILE"
}

auth_secret=$(awk -F= '$1 == "AUTH_SECRET" { sub(/^AUTH_SECRET=/, ""); print; exit }' "$ENV_FILE")
if [ -z "$auth_secret" ] || [ "$auth_secret" = "change-me-in-production-with-at-least-32-characters" ]; then
  replace_env AUTH_SECRET "$(openssl rand -hex 32)"
fi

youtube_key=$(awk -F= '$1 == "YOUTUBE_API_KEY" { sub(/^YOUTUBE_API_KEY=/, ""); print; exit }' "$ENV_FILE")
if [ -n "${YOUTUBE_API_KEY:-}" ]; then
  replace_env YOUTUBE_API_KEY "$YOUTUBE_API_KEY"
elif [ -z "$youtube_key" ] || [ "$youtube_key" = "replace-me" ]; then
  if [ -t 0 ]; then
    printf 'YouTube Data API key: '
    stty -echo
    read -r youtube_key
    stty echo
    printf '\n'
    replace_env YOUTUBE_API_KEY "$youtube_key"
  else
    echo "Set YOUTUBE_API_KEY or update $ENV_FILE before running quickstart." >&2
    exit 1
  fi
fi

docker compose --env-file "$ENV_FILE" run --rm migrate
docker compose --env-file "$ENV_FILE" up -d --build
./scripts/health.sh

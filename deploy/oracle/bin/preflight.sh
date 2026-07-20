#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
# shellcheck source=common.sh
. "$SCRIPT_DIR/common.sh"

require_root
load_env

[ "${APP_ENV:-}" = "production" ] || die "APP_ENV must be production."
[ "${APP_MODE:-}" = "full" ] || die "APP_MODE must be full."

printf '%s' "${CHOOSEYOURTUBE_VERSION:-}" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?$' \
  || die "CHOOSEYOURTUBE_VERSION must be an exact semantic version such as 1.0.0."
printf '%s' "${CADDY_VERSION:-}" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$' \
  || die "CADDY_VERSION must be an exact semantic version such as 2.11.4."

printf '%s' "${APP_DOMAIN:-}" | grep -Eq '^[A-Za-z0-9]([A-Za-z0-9.-]*[A-Za-z0-9])?$' \
  || die "APP_DOMAIN must be a DNS hostname without a scheme or path."
[ "${APP_DOMAIN:-}" != "tube.example.com" ] || die "Replace the example APP_DOMAIN."
[ "${API_ORIGIN:-}" = "https://${APP_DOMAIN}" ] \
  || die "API_ORIGIN must exactly equal https://APP_DOMAIN."
[ "${API_CORS_ORIGINS:-}" = "https://${APP_DOMAIN}" ] \
  || die "API_CORS_ORIGINS must exactly equal https://APP_DOMAIN."
printf '%s' "${ACME_EMAIL:-}" | grep -Eq '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$' \
  || die "ACME_EMAIL must be a valid administrator email."
[ "${ACME_EMAIL:-}" != "admin@example.com" ] || die "Replace the example ACME_EMAIL."
[ -n "${YOUTUBE_API_KEY:-}" ] && [ "${YOUTUBE_API_KEY}" != "replace-me" ] \
  || die "Set YOUTUBE_API_KEY."
[ "${#AUTH_SECRET}" -ge 32 ] && [ "$AUTH_SECRET" != "replace-me" ] \
  || die "AUTH_SECRET must contain at least 32 characters."
printf '%s' "${POSTGRES_USER:-}" | grep -Eq '^[A-Za-z_][A-Za-z0-9_-]*$' \
  || die "POSTGRES_USER contains unsupported characters."
printf '%s' "${POSTGRES_DB:-}" | grep -Eq '^[A-Za-z_][A-Za-z0-9_-]*$' \
  || die "POSTGRES_DB contains unsupported characters."
printf '%s' "${POSTGRES_PASSWORD:-}" | grep -Eq '^[A-Za-z0-9_-]{24,}$' \
  || die "POSTGRES_PASSWORD must be 24+ URL-safe characters."

case "$(uname -m)" in
  x86_64|aarch64) ;;
  *) die "Only x86_64 and aarch64 hosts are supported." ;;
esac

memory_kb=$(awk '/^MemTotal:/ { print $2 }' /proc/meminfo)
disk_kb=$(df -Pk "$REPO_DIR" | awk 'NR == 2 { print $4 }')
if [ "${ALLOW_LOW_RESOURCE:-false}" != "true" ]; then
  [ "$memory_kb" -ge 2097152 ] || die "At least 2 GB RAM is required; set ALLOW_LOW_RESOURCE=true to override."
  [ "$disk_kb" -ge 10485760 ] || die "At least 10 GB free disk is required; set ALLOW_LOW_RESOURCE=true to override."
fi

docker compose version >/dev/null 2>&1 || die "Docker Compose is not installed."
compose_version=$(docker compose version --short | sed 's/[^0-9.].*$//')
dpkg --compare-versions "$compose_version" ge 2.24.4 \
  || die "Docker Compose 2.24.4 or newer is required."
compose config --quiet

if ! compose ps --status running --quiet caddy | grep -q .; then
  for port in 80 443; do
    if ss -H -ltn "sport = :$port" 2>/dev/null | grep -q .; then
      die "TCP port $port is already in use."
    fi
  done
fi

if ! getent ahosts "$APP_DOMAIN" >/dev/null 2>&1; then
  log "Warning: $APP_DOMAIN does not resolve yet; Caddy cannot issue a certificate until DNS is ready."
fi

log "Oracle VM deployment preflight passed."

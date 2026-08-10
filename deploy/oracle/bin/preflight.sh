#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
# shellcheck source=common.sh
. "$SCRIPT_DIR/common.sh"

require_root
load_env

printf '%s' "${APP_DOMAIN:-}" | grep -Eq '^[A-Za-z0-9]([A-Za-z0-9.-]*[A-Za-z0-9])?$' \
  || die "APP_DOMAIN must be a DNS hostname without a scheme or path."
[ "${APP_DOMAIN:-}" != "tube.example.com" ] || die "Replace the example APP_DOMAIN."
printf '%s' "${ACME_EMAIL:-}" | grep -Eq '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$' \
  || die "ACME_EMAIL must be a valid administrator email."
if [ "${ACME_EMAIL:-}" = "admin@example.com" ] \
  || [ "${ACME_EMAIL:-}" = "your-email@example.com" ]; then
  die "Replace the example ACME_EMAIL."
fi
if [ -z "${YOUTUBE_API_KEY:-}" ] || [ "${YOUTUBE_API_KEY}" = "replace-me" ]; then
  die "Set YOUTUBE_API_KEY."
fi
if [ "${#AUTH_SECRET}" -lt 32 ] \
  || [ "$AUTH_SECRET" = "replace-me" ] \
  || [ "$AUTH_SECRET" = "change-me-in-production-with-at-least-32-characters" ]; then
  die "AUTH_SECRET must contain at least 32 characters."
fi
[ -n "${REGISTRATION_EMAIL_ALLOWLIST:-}" ] \
  || die "Set REGISTRATION_EMAIL_ALLOWLIST to one or more exact email addresses."
old_ifs=$IFS
IFS=,
for registration_email in $REGISTRATION_EMAIL_ALLOWLIST; do
  printf '%s' "$registration_email" | grep -Eq '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$' \
    || die "REGISTRATION_EMAIL_ALLOWLIST must contain comma-separated exact email addresses."
  [ "$registration_email" != "your-login-email@example.com" ] \
    || die "Replace the example REGISTRATION_EMAIL_ALLOWLIST."
done
IFS=$old_ifs
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
  [ "$memory_kb" -ge 6291456 ] || die "At least 6 GB RAM is required to build and run the source deployment; set ALLOW_LOW_RESOURCE=true to override."
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

log "Production deployment preflight passed."

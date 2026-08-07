#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
# shellcheck source=common.sh
. "$SCRIPT_DIR/common.sh"

require_root
load_env

compose ps
compose exec -T backend python -c \
  "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=5).read(); urllib.request.urlopen('http://127.0.0.1:8000/health/ready', timeout=5).read()"
compose exec -T frontend node -e \
  "fetch('http://127.0.0.1:5173/api/meta').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"
compose exec -T redis redis-cli ping | grep -q PONG
compose exec -T redis redis-cli exists chooseyourtube:worker:heartbeat | grep -q 1
compose exec -T postgres sh -c 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"' >/dev/null
compose ps --status running --quiet caddy | grep -q .

attempt=0
until curl --fail --silent --show-error --max-time 10 "https://${APP_DOMAIN}/api/meta" >/dev/null; do
  attempt=$((attempt + 1))
  [ "$attempt" -lt 36 ] || die "Public HTTPS health check failed for https://${APP_DOMAIN}/api/meta. Check DuckDNS and OCI ingress for ports 80 and 443."
  sleep 5
done

log "ChooseYourTube is healthy at https://${APP_DOMAIN}."

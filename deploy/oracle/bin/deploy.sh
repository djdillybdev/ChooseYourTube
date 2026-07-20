#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)

"$SCRIPT_DIR/preflight.sh"
# shellcheck source=common.sh
. "$SCRIPT_DIR/common.sh"
load_env

compose pull
compose run --rm --no-deps caddy caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
compose up -d --wait --remove-orphans
"$SCRIPT_DIR/health.sh"

log "ChooseYourTube ${CHOOSEYOURTUBE_VERSION} is deployed at https://${APP_DOMAIN}."

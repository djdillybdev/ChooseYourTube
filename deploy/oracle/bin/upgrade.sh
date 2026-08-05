#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
# shellcheck source=common.sh
. "$SCRIPT_DIR/common.sh"

require_root
[ "$#" -eq 1 ] || die "Usage: $0 NEW_VERSION"
new_version=$1
printf '%s' "$new_version" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?$' \
  || die "NEW_VERSION must be an exact semantic version such as 1.1.0."

load_env
[ "$new_version" != "$CHOOSEYOURTUBE_VERSION" ] || die "Version $new_version is already configured."
"$SCRIPT_DIR/backup.sh"
replace_env_value CHOOSEYOURTUBE_VERSION "$new_version"

if ! "$SCRIPT_DIR/deploy.sh"; then
  die "Upgrade failed. The new version remains configured; inspect logs before attempting a migration-aware rollback."
fi

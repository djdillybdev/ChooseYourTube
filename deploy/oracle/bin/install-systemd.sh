#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
# shellcheck source=common.sh
. "$SCRIPT_DIR/common.sh"

require_root
[ "$REPO_DIR" = "/opt/chooseyourtube" ] \
  || die "Systemd installation requires the repository at /opt/chooseyourtube."
[ -f "$ENV_FILE" ] || die "Run configure.sh before installing systemd units."

install -m 0644 "$REPO_DIR/deploy/oracle/systemd/chooseyourtube.service" /etc/systemd/system/chooseyourtube.service
install -m 0644 "$REPO_DIR/deploy/oracle/systemd/chooseyourtube-backup.service" /etc/systemd/system/chooseyourtube-backup.service
install -m 0644 "$REPO_DIR/deploy/oracle/systemd/chooseyourtube-backup.timer" /etc/systemd/system/chooseyourtube-backup.timer
systemctl daemon-reload
systemctl enable --now chooseyourtube.service chooseyourtube-backup.timer

log "Systemd units installed and enabled."

#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)

[ -f "$SCRIPT_DIR/../../../.env" ] || {
  printf '%s\n' "Error: missing .env." >&2
  printf '%s\n' "Run: cp deploy/oracle/oracle.env.example .env" >&2
  printf '%s\n' "Then edit .env and rerun: sudo ./chooseyourtube setup" >&2
  exit 1
}

"$SCRIPT_DIR/install-host.sh"

legacy_units_removed=false
for legacy_unit in \
  chooseyourtube.service \
  chooseyourtube-backup.service \
  chooseyourtube-backup.timer; do
  legacy_unit_path="/etc/systemd/system/$legacy_unit"
  if [ -e "$legacy_unit_path" ]; then
    systemctl disable --now "$legacy_unit" >/dev/null 2>&1 || true
    rm -f "$legacy_unit_path"
    legacy_units_removed=true
  fi
done
if [ "$legacy_units_removed" = "true" ]; then
  systemctl daemon-reload
  printf '%s\n' "Removed legacy ChooseYourTube systemd units; Docker restart policies now manage startup."
fi

"$SCRIPT_DIR/configure.sh"
"$SCRIPT_DIR/deploy.sh"

printf '\nChooseYourTube setup is complete.\n'
printf 'Useful commands:\n'
printf '  sudo ./chooseyourtube status\n'
printf '  sudo ./chooseyourtube logs\n'
printf '  sudo ./chooseyourtube backup\n'

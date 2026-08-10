#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
# shellcheck source=common.sh
. "$SCRIPT_DIR/common.sh"

require_root
[ -r /etc/os-release ] || die "Cannot identify the host operating system."
# shellcheck disable=SC1091
. /etc/os-release
if [ "${ID:-}" != "ubuntu" ] || [ "${VERSION_ID:-}" != "24.04" ]; then
  die "This installer supports Ubuntu 24.04 only."
fi

apt-get update
apt-get install -y ca-certificates curl git gnupg openssl

if command -v docker >/dev/null 2>&1; then
  docker compose version >/dev/null 2>&1 \
    || die "Docker is already installed without the Compose plugin; install a compatible Compose plugin without replacing the existing engine."
  compose_version=$(docker compose version --short | sed 's/[^0-9.].*$//')
  dpkg --compare-versions "$compose_version" ge 2.24.4 \
    || die "Docker Compose 2.24.4 or newer is required."
  systemctl enable --now docker.service
  log "Existing Docker Engine and Compose $compose_version are compatible; no packages were changed."
  exit 0
fi

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

architecture=$(dpkg --print-architecture)
codename=$VERSION_CODENAME
printf '%s\n' \
  "deb [arch=$architecture signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $codename stable" \
  > /etc/apt/sources.list.d/docker.list

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable --now docker.service containerd.service
docker version >/dev/null
docker compose version >/dev/null
compose_version=$(docker compose version --short | sed 's/[^0-9.].*$//')
dpkg --compare-versions "$compose_version" ge 2.24.4 \
  || die "Docker Compose 2.24.4 or newer is required."

log "Docker and Compose $compose_version are installed and enabled. Host and OCI firewall rules were left unchanged."

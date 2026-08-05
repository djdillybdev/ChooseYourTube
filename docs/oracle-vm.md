# Deploy on an Oracle Cloud VM

This guide installs the full ChooseYourTube stack on an Ubuntu 24.04 Oracle Cloud Infrastructure
(OCI) VM. It uses published `amd64` or `arm64` images, Caddy-managed HTTPS, private Docker networking,
systemd startup, resource limits, and scheduled PostgreSQL backups.

## Requirements

- Ubuntu 24.04 on `x86_64` or Ampere `aarch64`;
- at least 2 GB RAM and 10 GB free persistent storage;
- a reserved public IP and a domain whose `A` record points to it;
- TCP ports 80 and 443 available on the VM;
- an exact ChooseYourTube release version;
- a YouTube Data API key.

The default limits permit the containers to use up to approximately 3.3 GB combined. Limits are
ceilings, not reservations. Review them in `.env` if the VM has constrained resources.

## Prepare OCI networking

Assign a [reserved public IP](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/managingpublicIPs.htm)
to the VM and point the deployment domain to it. Add stateful ingress rules to the VM's Network
Security Group for:

| Source                       | Protocol | Destination | Purpose                            |
| ---------------------------- | -------- | ----------- | ---------------------------------- |
| `0.0.0.0/0`                  | TCP      | 80          | ACME validation and HTTPS redirect |
| `0.0.0.0/0`                  | TCP      | 443         | Application HTTPS                  |
| trusted administrator ranges | TCP      | 22          | SSH administration                 |

Apply equivalent allowances to the host firewall without replacing existing rules. OCI networking
and the host firewall are both enforced. Do not open 5173, 8000, 5432, or 6379; production Compose
removes the application port publications and exposes only Caddy.

## Install and configure

### Ansible-managed installation

For repeatable deployment and day-two management from a macOS or Linux controller, use the
[Ansible control layer](../deploy/ansible/README.md). It configures an existing Ubuntu VM, manages the
registration allowlist and exact release, performs pre-upgrade backups, verifies health, fetches
off-host backups, and provides a guarded restore workflow. OCI networking, the reserved IP, and DNS
remain prerequisites.

### Manual installation

Clone an exact release into the fixed systemd path. Replace `v1.0.0` with the intended release:

```bash
sudo git clone --branch v1.0.0 --depth 1 \
  https://github.com/djdillybdev/ChooseYourTube.git /opt/chooseyourtube
cd /opt/chooseyourtube
sudo ./deploy/oracle/bin/install-host.sh
sudo ./deploy/oracle/bin/configure.sh
sudoedit /opt/chooseyourtube/.env
```

Set these required values in `.env`:

```env
CHOOSEYOURTUBE_VERSION=1.0.0
CADDY_VERSION=2.11.4
APP_DOMAIN=tube.example.com
ACME_EMAIL=admin@example.com
API_ORIGIN=https://tube.example.com
API_CORS_ORIGINS=https://tube.example.com
YOUTUBE_API_KEY=your-key
```

`configure.sh` generates `AUTH_SECRET` and a URL-safe PostgreSQL password without displaying them.
The environment file must remain owned by root with mode `0600`.

Registration is enabled by default and the Oracle profile requires a non-empty allowlist.
`REGISTRATION_EMAIL_ALLOWLIST` accepts comma-separated complete addresses and compares them
case-insensitively:

```env
REGISTRATION_EMAIL_ALLOWLIST=person@example.com,second@example.com
```

The root-only helper updates the list without displaying or changing other secrets:

```bash
sudo ./deploy/oracle/bin/allowlist.sh list
sudo ./deploy/oracle/bin/allowlist.sh add another@example.com
sudo ./deploy/oracle/bin/allowlist.sh remove person@example.com
```

Wildcards and domain-only entries are not supported. The deployment preflight and application startup
both reject enabled registration with an empty list. To stop onboarding after the invited users have
registered, set `REGISTRATION_ENABLED=false`; existing users can still sign in. Removing an address
from the list prevents a new registration but does not deactivate an existing account.

After changing either registration setting, apply it with:

```bash
sudo systemctl restart chooseyourtube
```

## Deploy and enable boot startup

Wait for DNS to resolve to the VM, then run:

```bash
cd /opt/chooseyourtube
sudo ./deploy/oracle/bin/deploy.sh
sudo ./deploy/oracle/bin/install-systemd.sh
```

The deployment validates configuration, architecture, memory, disk, DNS, ports, Compose, and Caddy;
pulls the exact release; runs database migrations; waits for healthy containers; and checks the
public HTTPS endpoint. It does not build images or change firewall rules.

Useful operations:

```bash
sudo systemctl status chooseyourtube
sudo systemctl reload chooseyourtube
sudo make oracle-health
sudo make oracle-logs
sudo make oracle-backup
sudo systemctl list-timers chooseyourtube-backup.timer
```

After a VM reboot, verify `systemctl status chooseyourtube`, `sudo make oracle-health`, and the public
site. Caddy stores certificates in its named Docker volume and renews them automatically.

## Optional Google OAuth import

Google Takeout CSV import needs no OAuth configuration. To enable one-time Google subscription
discovery, create a Google web OAuth client and set:

```env
YOUTUBE_OAUTH_ENABLED=true
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=https://tube.example.com/imports/youtube/oauth/callback
```

Register that exact HTTPS URI in Google Cloud, then reload the service. Caddy proxies only this exact
callback path directly to FastAPI; all normal browser API traffic continues through SvelteKit.

## Backups and restore

The systemd timer creates a custom-format PostgreSQL dump daily at 03:15 UTC plus a random delay of
up to 30 minutes. Dumps are mode `0600` under `/var/backups/chooseyourtube` and are retained for 14
days by default. Cleanup runs only after a new non-empty dump succeeds.

Change `BACKUP_DIR` or `BACKUP_RETENTION_DAYS` in `.env` if needed. These backups remain on the VM and
do not protect against loss of the VM or its storage. Copy important dumps to another system.

Test a restore on a separate installation. Restoring replaces the current database:

```bash
cd /opt/chooseyourtube
sudo CONFIRM=RESTORE \
  BACKUP_FILE=/var/backups/chooseyourtube/chooseyourtube-20260720T031500Z.dump \
  ./deploy/oracle/bin/restore.sh
```

The restore stops writers and Caddy, recreates the configured database, restores the dump, applies
current migrations, restarts the stack, and runs health checks.

## Upgrade and rollback

Read the target release notes and migration notes, then pass an exact version:

```bash
cd /opt/chooseyourtube
sudo ./deploy/oracle/bin/upgrade.sh 1.1.0
```

The upgrade refuses floating versions, creates a backup, records the new version, pulls its images,
runs migrations, and verifies health. It does not automatically roll back after a failed migration.
An older image can be restarted only when it understands the migrated schema; otherwise restore the
pre-upgrade dump with the matching source release.

Deployment scripts themselves are versioned with the repository. For a later release, update the
checkout to the matching tag before running its upgrade script.

## Troubleshooting

- Run `sudo ./deploy/oracle/bin/preflight.sh` for configuration and capacity errors.
- Check `sudo docker compose --env-file .env -f compose.yaml -f compose.release.yaml -f deploy/oracle/compose.yaml ps`.
- Read `sudo journalctl -u chooseyourtube` and `sudo make oracle-logs`.
- If TLS issuance fails, confirm public DNS and both OCI and host firewall rules for ports 80/443.
- If the worker is unhealthy, inspect Redis connectivity and `BACKGROUND_JOBS_ENABLED=true`.
- Inspect pressure with `free -h`, `df -h`, and `sudo docker stats` before raising resource limits.
- Use `ALLOW_LOW_RESOURCE=true` only to bypass the preflight minimum; it does not reduce the stack's
  actual requirements.

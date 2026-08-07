# Host ChooseYourTube on an Oracle Cloud VM

This is the supported production path for an Ubuntu 24.04 Oracle Cloud Infrastructure (OCI) VM. It
builds the cloned checkout, runs the complete application with Docker Compose, and serves it through
Caddy-managed HTTPS.

The setup command supports both Ampere `aarch64` and `x86_64`. Use at least 6 GB RAM and 10 GB free
disk space so the VM can build the frontend and backend while the database and worker are running.

## 1. Prepare Oracle networking

Use a stable or reserved public IPv4 address. In the Network Security Group attached to the VM, or
in its subnet security list, add these stateful ingress rules:

| Source | Protocol | Destination port | Purpose |
| --- | --- | --- | --- |
| `0.0.0.0/0` | TCP | `80` | Certificate validation and HTTPS redirect |
| `0.0.0.0/0` | TCP | `443` | Public HTTPS application |
| your administrator CIDR | TCP | `22` | SSH administration |

Do not open ports 5173, 8000, 5432, or 6379. The production Compose configuration publishes only
Caddy; the frontend, API, PostgreSQL, and Redis stay on the private Docker network.

Do not enable UFW on an OCI Ubuntu platform image. Oracle warns that UFW can remove essential
platform firewall rules and prevent a successful reboot. Preserve the image's existing host rules
and use the OCI network rules above. If the image has custom host firewall rules, arrange equivalent
allowances for ports 80 and 443 without replacing Oracle's essential rules.

## 2. Confirm DuckDNS

Set the DuckDNS IPv4 address for `chooseyourtube.duckdns.org` to the VM's public IPv4 address. From
your laptop or desktop, confirm it before deploying:

```bash
dig +short A chooseyourtube.duckdns.org
```

The result must be the VM address. Remove a stale `AAAA` record unless the VM is intentionally
configured and secured for IPv6. Caddy needs correct DNS and public access to ports 80 and 443 to
obtain and renew the HTTPS certificate.

## 3. Clone and configure ChooseYourTube

SSH into the VM as its normal Ubuntu account, then run:

```bash
git clone https://github.com/djdillybdev/ChooseYourTube.git
cd ChooseYourTube
cp deploy/oracle/oracle.env.example .env
nano .env
```

Set the four required values:

```env
APP_DOMAIN=chooseyourtube.duckdns.org
ACME_EMAIL=you@example.com
YOUTUBE_API_KEY=your-youtube-data-api-key
REGISTRATION_EMAIL_ALLOWLIST=you@example.com
```

The allowlist accepts comma-separated complete email addresses and is case-insensitive. Only those
addresses can create accounts. Do not add spaces around commas.

Google Takeout CSV import works without OAuth. Leave the OAuth values disabled for the first setup.

## 4. Set up and host the application

Run the one setup command from the repository root:

```bash
sudo ./chooseyourtube setup
```

The command:

1. validates Ubuntu, architecture, memory, disk, configuration, DNS, and ports;
2. installs Docker Engine and the Compose plugin from Docker's official Ubuntu repository when
   needed;
3. generates the authentication and PostgreSQL secrets and protects `.env` with mode `0600`;
4. builds the current checkout and validates the Caddy configuration;
5. applies database migrations and starts the application; and
6. verifies internal services and the public HTTPS endpoint.

The first build and certificate request can take several minutes. When setup reports success, open:

<https://chooseyourtube.duckdns.org>

Register using an address in `REGISTRATION_EMAIL_ALLOWLIST`. The same URL works from laptops,
desktops, and phones on any network.

Docker is enabled at boot, and the long-running containers use `unless-stopped` restart policies.
No separate application systemd service is installed.

## Operations

Run management commands from the cloned repository:

```bash
sudo ./chooseyourtube status
sudo ./chooseyourtube logs
sudo ./chooseyourtube restart
sudo ./chooseyourtube stop
sudo ./chooseyourtube start
```

`stop` preserves PostgreSQL, Redis, and Caddy volumes. After a reboot, use `status` to verify the
stack and its public endpoint.

### Update the application

Pull code as the normal repository owner, then rerun the same idempotent setup command:

```bash
git pull --ff-only
sudo ./chooseyourtube setup
```

The command rebuilds changed images, reapplies migrations, and preserves secrets and named volumes.
Create a backup before an update that includes database migrations.

### Back up and restore

Create a manual PostgreSQL backup:

```bash
sudo ./chooseyourtube backup
```

The command prints the absolute path of the new custom-format dump. Backups are not scheduled or
automatically deleted. Copy important dumps off the VM.

Restore replaces the current database. Test restores on a separate installation whenever possible:

```bash
sudo CONFIRM=RESTORE ./chooseyourtube restore \
  /var/backups/chooseyourtube/chooseyourtube-20260807T120000Z.dump
```

Restore validates the dump, stops application writers, recreates PostgreSQL, reapplies migrations,
restarts the stack, and runs health checks.

### Change allowed registration addresses

The helper updates the root-only `.env` without printing other secrets:

```bash
sudo ./deploy/oracle/bin/allowlist.sh list
sudo ./deploy/oracle/bin/allowlist.sh add another@example.com
sudo ./deploy/oracle/bin/allowlist.sh remove another@example.com
sudo ./chooseyourtube restart
```

Removing an address prevents future registration but does not deactivate an existing account.

## Optional Google OAuth import

To enable one-time Google subscription discovery, create a Google web OAuth client and add:

```env
YOUTUBE_OAUTH_ENABLED=true
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=https://chooseyourtube.duckdns.org/imports/youtube/oauth/callback
```

Register that exact HTTPS redirect URI in Google Cloud, then run `sudo ./chooseyourtube restart`.
Caddy sends only that callback path directly to FastAPI; normal browser API traffic stays behind
SvelteKit.

## Troubleshooting

- If setup says the domain does not resolve, correct DuckDNS and wait for DNS propagation.
- If public HTTPS fails, verify both OCI ingress rules and confirm no other process uses ports 80 or
  443 with `sudo ss -ltnp`.
- Run `sudo ./chooseyourtube status` for service readiness and `sudo ./chooseyourtube logs` for
  migration, Caddy, worker, or authentication errors.
- Check capacity with `free -h`, `df -h`, and `sudo docker stats`. `ALLOW_LOW_RESOURCE=true` bypasses
  preflight only; it does not reduce actual build or runtime requirements.
- If Docker is already installed without a compatible Compose plugin, setup stops without replacing
  the existing engine. Resolve that installation explicitly, then rerun setup.
- Never use `docker compose down --volumes` unless permanently deleting application data is intended.

# Manage ChooseYourTube with Ansible

This control layer configures one existing Ubuntu 24.04 Oracle Cloud VM and manages the complete
ChooseYourTube lifecycle over SSH. It does not create OCI networking, compute instances, reserved IPs,
or DNS records.

For a first deployment beginning with an empty OCI account and ending with registration and login on
a Mac, follow the [complete Oracle Cloud runbook](../../docs/oracle-ansible-runbook.md). This document
is the shorter day-two reference for an already prepared host.

## Controller setup

Use macOS or Linux with Python 3.12 or newer:

```bash
cd deploy/ansible
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
ansible-galaxy collection install -r requirements.yml
```

Ansible uses SSH host-key checking. Connect to the VM once and verify its fingerprint through the OCI
console before running a playbook.

## Inventory and secrets

Create the ignored local inventory and Vault file:

```bash
cp inventory/production/hosts.yml.example inventory/production/hosts.yml
cp inventory/production/group_vars/chooseyourtube/main.yml.example \
  inventory/production/group_vars/chooseyourtube/main.yml
cp inventory/production/group_vars/chooseyourtube/vault.yml.example \
  inventory/production/group_vars/chooseyourtube/vault.yml
ansible-vault encrypt inventory/production/group_vars/chooseyourtube/vault.yml
```

Edit `hosts.yml` with the reserved public IP or DNS name. Edit `group_vars/chooseyourtube/main.yml`
with the exact release version, domain, ACME email, and invited registration addresses. Use
`ansible-vault edit` to replace all required secrets. Generate strong local values with:

```bash
openssl rand -hex 32  # AUTH_SECRET
openssl rand -hex 24  # POSTGRES_PASSWORD
```

The inventory, production variables, encrypted Vault, and Vault password are required to recreate the
deployment. Back them up separately. The repository ignores the local production files, keeping the
server address, invited email addresses, and secrets out of the public source tree.

## First deployment

Prepare the OCI Network Security Group and DNS as described in [the Oracle VM guide](../../docs/oracle-vm.md).
Only TCP 80 and 443 should be public; restrict TCP 22 to administrator networks. Then validate and
deploy:

```bash
ansible-playbook playbooks/validate.yml --ask-vault-pass
ansible-playbook playbooks/site.yml --ask-vault-pass
```

Secret template tasks suppress output even with `--diff`. The deployment installs Docker from its
official Ubuntu repository, checks out the exact `vX.Y.Z` application tag, renders the root-only
environment, pulls matching images, runs migrations, enables systemd startup and backups, and verifies
internal and public health.

After the first deployment, preview later configuration or release changes with
`ansible-playbook playbooks/site.yml --check --diff --ask-vault-pass`. A pristine host cannot fully
simulate packages and release files that have not been installed yet.

The chosen tag and matching `amd64`/`arm64` GHCR images must already exist. Public packages need no
registry credentials. If packages are private, put the optional GHCR username and token in Vault.

## Configuration and upgrades

Ansible is authoritative for `/opt/chooseyourtube/.env`. Change variables in the inventory and rerun
`site.yml`; manual environment or allowlist changes are overwritten. The existing root-only
`allowlist.sh` remains available only for emergency changes that are immediately copied back into the
inventory.

To upgrade, change `chooseyourtube_version` to another exact released version and rerun `site.yml`.
When the deployed version changes, Ansible creates a database backup before checking out the new tag.
It records the new version only after migrations and health checks pass. Migration failures are not
automatically rolled back; inspect the reported backup and release compatibility before restoring.

## Health, backup, and restore

```bash
ansible-playbook playbooks/health.yml --ask-vault-pass
ansible-playbook playbooks/backup_fetch.yml --ask-vault-pass
ansible-playbook playbooks/restore.yml --ask-vault-pass \
  -e restore_confirm=RESTORE \
  -e restore_source=/absolute/controller/path/chooseyourtube.dump
```

`backup_fetch.yml` creates a fresh custom-format PostgreSQL dump, verifies SHA-256 before and after
transfer, and stores it under `deploy/ansible/backups/<inventory-host>/` by default. Override the local
directory with `-e chooseyourtube_controller_backup_dir=/absolute/path`.

Restore replaces the production database. It accepts only an absolute, non-empty controller-side
dump, verifies the staged checksum, invokes the guarded restore workflow, checks application health,
and removes its temporary remote copy.

## Optional UFW management

UFW is disabled by default. To enable it, first set every trusted SSH source in CIDR notation and then
enable management:

```yaml
chooseyourtube_manage_ufw: true
chooseyourtube_admin_cidrs:
  - "198.51.100.24/32"
```

The role adds rate-limited SSH rules before enabling a default-deny incoming policy and public 80/443.
It removes SSH CIDRs previously managed by the role when they leave the list. OCI NSG rules remain a
separate control and must agree with the host firewall. Docker can bypass some UFW forwarding rules,
but the production Compose overlay publishes only the intended Caddy ports.

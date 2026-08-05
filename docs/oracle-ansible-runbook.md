# Oracle Cloud to first login: complete deployment runbook

This runbook takes ChooseYourTube from the repository to a production Oracle Cloud Infrastructure
(OCI) VM, then finishes with registration and login from a Mac. Ansible performs the repeatable host
and application configuration. The OCI instance, network, reserved IP, DNS record, Google API key,
and release publication are created outside Ansible.

Follow the sections in order for the first deployment. Commands are run on the **Mac** unless a step
explicitly says **OCI Console** or **Oracle VM**.

## 1. Collect the deployment values

Choose these values before starting. This runbook uses the examples in the right column:

| Value | Meaning | Example |
| --- | --- | --- |
| `RELEASE_VERSION` | Exact application version, without `v` | `1.0.0` |
| `APP_DOMAIN` | Public application hostname | `tube.example.com` |
| `ACME_EMAIL` | Certificate-expiry contact | `admin@example.com` |
| `LOGIN_EMAIL` | First address allowed to register | `you@example.com` |
| `OCI_REGION` | Region containing the VM and reserved IP | `eu-madrid-1` |
| `VM_PUBLIC_IP` | Reserved public IPv4 address | assigned later |
| `SSH_KEY` | Private key path on the Mac | `/Users/you/.ssh/chooseyourtube_oracle` |
| `MAC_PUBLIC_IP` | Current public IPv4 address of the Mac's network | `198.51.100.24` |

Use a hostname dedicated to this service. Do not use an apex domain if other services already use it.
The email allowlist accepts complete addresses only; it does not accept wildcards or whole domains.

You need:

- an OCI account allowed to create Compute and Networking resources;
- control of the DNS zone for `APP_DOMAIN`;
- access to the GitHub repository and its Actions and package settings;
- a Google account that can create a project and a YouTube Data API key;
- macOS with Git, OpenSSH, Python 3.12 or newer, and about 1 GB free for controller dependencies.

## 2. Publish a deployable release

Ansible does not build production images on the VM. It checks out `vRELEASE_VERSION` and pulls the
same exact version of these multi-architecture images:

```text
ghcr.io/djdillybdev/chooseyourtube-backend:RELEASE_VERSION
ghcr.io/djdillybdev/chooseyourtube-frontend:RELEASE_VERSION
```

The current first-release workflow is prepared for `v1.0.0`. Before tagging it, merge the deployment
work into the commit intended for production and run the repository's release checks. From a clean
checkout on the Mac:

```bash
git status --short
make test
```

Push the branch, merge it through the normal review workflow, then update the local default branch.
Confirm that the commit contains `deploy/ansible` and the Oracle deployment files before tagging:

```bash
git switch main
git pull --ff-only origin main
git fetch --tags origin
test -f deploy/ansible/playbooks/site.yml
test -f deploy/oracle/bin/deploy.sh
git status --short
git tag -a v1.0.0 -m "ChooseYourTube v1.0.0"
git push origin v1.0.0
```

If `git status --short` prints anything, stop and resolve it before tagging. For a later release,
update all application-version and release-note assets as part of that release and use its version in
every step below.

In GitHub, open **Actions**, select **Release containers**, and wait for both the backend and frontend
image jobs to pass. Then open the owner's **Packages** page and confirm that both packages have a
`1.0.0` tag and support `linux/amd64` and `linux/arm64`.

The current Ansible checkout uses public HTTPS Git access. Make the repository public for this
deployment. Making the two GHCR packages public is also the simplest configuration. If the packages
remain private, Ansible supports a GHCR username and read token in Vault; a private Git repository,
however, needs deploy-key support that is not part of the current automation.

**Checkpoint:** the exact Git tag and both matching container tags are visible before creating the VM.

## 3. Prepare the Mac

### Create a dedicated SSH key

Do not overwrite an existing key. Replace `/Users/you` with the Mac account's actual home path:

```bash
ssh-keygen -t ed25519 -a 100 -f /Users/you/.ssh/chooseyourtube_oracle \
  -C "chooseyourtube-oracle"
chmod 600 /Users/you/.ssh/chooseyourtube_oracle
pbcopy < /Users/you/.ssh/chooseyourtube_oracle.pub
```

Use a key passphrase and store it in the macOS Keychain or a password manager. The public key is now
on the clipboard for the OCI instance form. The private key never leaves the Mac.

### Find the administrator source address

From the network where deployments will normally run:

```bash
curl -4 https://icanhazip.com
```

Record the returned address as `MAC_PUBLIC_IP`. The OCI SSH rule will use
`MAC_PUBLIC_IP/32`, allowing only that one IPv4 address. If the ISP changes it later, update the OCI
rule before trying SSH. A VPN changes the visible address; either keep the VPN state consistent or
record the appropriate trusted CIDR.

### Install the controller prerequisites

Check the existing tools first:

```bash
git --version
ssh -V
python3 --version
```

The Ansible requirements need Python 3.12 or newer. If it is missing and Homebrew is already used on
the Mac:

```bash
brew install python@3.12 git
```

## 4. Create the OCI network and VM

Oracle recommends creating a VCN first; its **Start VCN Wizard** can create a VCN with internet
connectivity, public and private subnets, an internet gateway, and route rules. OCI requires an
internet gateway, suitable route rules, a public subnet, and a public IP for direct internet access.
See Oracle's [instance creation guide](https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/launchinginstance.htm)
and [public IP overview](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/managingpublicIPs.htm).

### Create the VCN

In the **OCI Console**:

1. Select the intended region and compartment. Keep the VCN, NSG, instance, and reserved IP in that
   region and preferably in the same compartment.
2. Open **Networking > Virtual Cloud Networks > Start VCN Wizard**.
3. Choose **Create VCN with Internet Connectivity**.
4. Name it `chooseyourtube-vcn`. The default non-overlapping private CIDRs are suitable for one VM.
5. Finish the wizard and retain the public subnet, internet gateway, and default route to it.

Do not enable IPv6 for this first deployment unless it will be secured and tested separately. Do not
publish an `AAAA` DNS record when the instance is configured only for IPv4.

### Create and attach a Network Security Group

An NSG is OCI's virtual firewall for selected VNICs. Create `chooseyourtube-web-nsg` in the new VCN
and add these **stateful ingress** rules:

| Source CIDR | IP protocol | Destination port | Purpose |
| --- | --- | --- | --- |
| `MAC_PUBLIC_IP/32` | TCP | `22` | SSH from the administrator network |
| `0.0.0.0/0` | TCP | `80` | ACME certificate validation and HTTPS redirect |
| `0.0.0.0/0` | TCP | `443` | Public HTTPS application |

Leave source ports as **All**. Retain stateful outbound internet access so the host can install
packages and pull images. Do not open ports 5173, 8000, 5432, or 6379. Oracle documents NSGs as a
virtual firewall whose rules apply to the VNICs assigned to the group; review the
[NSG overview](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/networksecuritygroups.htm)
if console labels differ.

If the public subnet's security list is more restrictive, it must also permit the same traffic.
Effective access is governed by the VCN route, security lists, NSG, and later any host firewall.

### Create the instance

In **Compute > Instances > Create instance**:

1. Name it `chooseyourtube-prod`.
2. Select **Canonical Ubuntu 24.04** as the platform image.
3. A practical small-production choice is `VM.Standard.A1.Flex` with 2 OCPUs and 8–12 GB RAM. The
   application supports both Ampere `aarch64` and `x86_64`; choose another available shape with at
   least 2 GB RAM if needed. The default container ceilings total about 3.3 GB, so 4 GB is a more
   realistic minimum and 8 GB provides operational headroom. OCI capacity and pricing vary by
   tenancy and region—verify the estimate shown by the console.
4. Select `chooseyourtube-vcn` and its **public subnet**.
5. Attach `chooseyourtube-web-nsg` to the primary VNIC.
6. Do not assign an ephemeral public IPv4 address if the form permits that choice; a reserved address
   is assigned next.
7. Paste the dedicated public SSH key copied from the Mac. Do not ask OCI to generate a replacement.
8. Use at least a 50 GB boot volume, with encryption enabled.
9. Create the instance and wait for **Running**.

Ubuntu instances use SSH key authentication rather than a login password. Oracle's
[key-pair guide](https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/managingkeypairs.htm)
documents Ed25519 support and keeping the private key on the client.

### Assign a reserved public IPv4 address

Open the new instance, then its primary VNIC and primary private IPv4 address. Edit its public-IP
assignment and create or select a **reserved public IP**, named `chooseyourtube-prod-ip`. If the
creation form assigned an ephemeral address, unassign it first; OCI does not convert an ephemeral
public-IP object into a reserved one.

Record the address as `VM_PUBLIC_IP`. Reserved public IPs persist independently of the instance and
can be reassigned within their region, unlike ephemeral addresses.

### Verify SSH and the host key

For a strong first-connection check, open the instance's **Resources > Run command** page in OCI,
create a shell-script command, and run this through Oracle Cloud Agent on the **Oracle VM**:

```bash
sudo ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

On the **Mac**, retrieve the presented fingerprint:

```bash
ssh-keyscan -t ed25519 VM_PUBLIC_IP 2>/dev/null | ssh-keygen -lf -
```

Replace `VM_PUBLIC_IP` in the command with the actual address. The SHA256 fingerprints must match.
Then connect once and accept the verified key:

```bash
ssh -i /Users/you/.ssh/chooseyourtube_oracle ubuntu@VM_PUBLIC_IP
```

Run `exit` to return to the Mac. A timeout usually means the NSG source CIDR is wrong, the VNIC is not
in the NSG, the subnet is not public, or its route to the internet gateway is missing.

**Checkpoint:** key-based SSH works from the Mac and the host fingerprint is in `~/.ssh/known_hosts`.

## 5. Point DNS at the reserved address

At the DNS provider for the domain, create:

| Type | Name | Value | Initial TTL |
| --- | --- | --- | --- |
| `A` | the chosen subdomain, such as `tube` | `VM_PUBLIC_IP` | `300` |

Remove conflicting `A` or `AAAA` records for the same hostname. Verify from the Mac:

```bash
dig +short A APP_DOMAIN
```

Replace `APP_DOMAIN` with the real hostname. Continue only when the result is exactly the reserved
public IP. Ports 80 and 443 must already be reachable so Caddy can obtain the TLS certificate during
deployment.

## 6. Create and restrict the YouTube API key

ChooseYourTube's server makes YouTube Data API requests. In the **Google Cloud Console**:

1. Create or select a dedicated project.
2. Open **APIs & Services > Library**, find **YouTube Data API v3**, and enable it.
3. Open **APIs & Services > Credentials > Create credentials > API key**.
4. Edit the new key. Under **Application restrictions**, choose **IP addresses** and add the reserved
   `VM_PUBLIC_IP`.
5. Under **API restrictions**, choose **Restrict key** and select only **YouTube Data API v3**.
6. Save it and copy the key directly into the encrypted Ansible Vault in the next section.

Google requires a project with the YouTube Data API enabled and an API key for unauthenticated public
data requests. Its [YouTube API introduction](https://developers.google.com/youtube/v3/getting-started)
also explains quota, while the [API-key restriction guide](https://docs.cloud.google.com/api-keys/docs/add-restrictions-api-keys)
distinguishes server IP restrictions from browser referrer restrictions. This application needs a
server IP restriction because calls originate from the Oracle VM, not the Mac browser.

The optional Google OAuth import is not needed for registration, login, or normal channel use. Leave
it disabled for the first deployment.

## 7. Configure Ansible on the Mac

Use the exact release checkout so the controller instructions match the deployed scripts:

```bash
cd /path/to/ChooseYourTube
git fetch --tags origin
git switch --detach v1.0.0
cd deploy/ansible
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
ansible-galaxy collection install -r requirements.yml
ansible --version
```

Replace `v1.0.0` with the chosen tag. A detached checkout is intentional for a deployment controller;
make inventory changes only in the ignored production files described below.

### Create the ignored production files

```bash
cp inventory/production/hosts.yml.example inventory/production/hosts.yml
cp inventory/production/group_vars/chooseyourtube/main.yml.example \
  inventory/production/group_vars/chooseyourtube/main.yml
cp inventory/production/group_vars/chooseyourtube/vault.yml.example \
  inventory/production/group_vars/chooseyourtube/vault.yml
```

Edit `inventory/production/hosts.yml` to contain the actual IP, username, and **absolute** private-key
path:

```yaml
---
all:
  children:
    chooseyourtube:
      hosts:
        tube.example.com:
          ansible_host: 203.0.113.10
          ansible_user: ubuntu
          ansible_ssh_private_key_file: /Users/you/.ssh/chooseyourtube_oracle
          ansible_python_interpreter: /usr/bin/python3
```

The host key (`tube.example.com`) is an Ansible label and should be the real application domain.
Replace the documentation IP and every example value.

Edit `inventory/production/group_vars/chooseyourtube/main.yml`:

```yaml
---
chooseyourtube_version: "1.0.0"
chooseyourtube_domain: "tube.example.com"
chooseyourtube_acme_email: "admin@example.com"

chooseyourtube_registration_enabled: true
chooseyourtube_registration_allowlist:
  - "you@example.com"

chooseyourtube_youtube_daily_quota_budget: 8000
chooseyourtube_youtube_oauth_enabled: false
chooseyourtube_google_redirect_uri: ""

chooseyourtube_manage_ufw: false
chooseyourtube_admin_cidrs: []
chooseyourtube_ssh_port: 22

chooseyourtube_backup_retention_days: 14
chooseyourtube_allow_low_resource: false

chooseyourtube_youtube_api_key: "{{ vault_chooseyourtube_youtube_api_key }}"
chooseyourtube_auth_secret: "{{ vault_chooseyourtube_auth_secret }}"
chooseyourtube_postgres_password: "{{ vault_chooseyourtube_postgres_password }}"
chooseyourtube_google_client_id: "{{ vault_chooseyourtube_google_client_id | default('') }}"
chooseyourtube_google_client_secret: "{{ vault_chooseyourtube_google_client_secret | default('') }}"
chooseyourtube_registry_username: "{{ vault_chooseyourtube_registry_username | default('') }}"
chooseyourtube_registry_token: "{{ vault_chooseyourtube_registry_token | default('') }}"
```

Keep UFW management off for the first run. The OCI NSG already restricts SSH. After deployment, UFW
can be enabled with the trusted administrator CIDR, but a changing home IP can otherwise lock out the
Mac.

### Fill and encrypt Vault

Generate two independent secrets on the Mac:

```bash
openssl rand -hex 32
openssl rand -hex 24
```

Copy the first output into `vault_chooseyourtube_auth_secret` and the second into
`vault_chooseyourtube_postgres_password`. Put the restricted YouTube key into
`vault_chooseyourtube_youtube_api_key`. Leave OAuth and registry values empty when those features are
unused:

```yaml
---
vault_chooseyourtube_youtube_api_key: "actual-restricted-google-key"
vault_chooseyourtube_auth_secret: "actual-64-character-output"
vault_chooseyourtube_postgres_password: "actual-48-character-output"
vault_chooseyourtube_google_client_id: ""
vault_chooseyourtube_google_client_secret: ""
vault_chooseyourtube_registry_username: ""
vault_chooseyourtube_registry_token: ""
```

Encrypt the file immediately:

```bash
ansible-vault encrypt inventory/production/group_vars/chooseyourtube/vault.yml
```

Use a strong, unique Vault password and store it in a password manager. Do not create a plaintext
Vault-password file in the repository. Verify the production files remain ignored:

```bash
git status --short --ignored \
  inventory/production/hosts.yml \
  inventory/production/group_vars/chooseyourtube/main.yml \
  inventory/production/group_vars/chooseyourtube/vault.yml
```

They should be shown as ignored, not tracked. Back up the encrypted Vault, inventory, variables, SSH
private key, and Vault password in secure locations. Together they are needed to recreate the host.

If the GHCR packages are private, set the registry username and a fine-grained token with package
read access in Vault. Do not use a broad personal token.

## 8. Validate and deploy

From `deploy/ansible` with the virtual environment active, first test SSH through Ansible:

```bash
ansible chooseyourtube -m ping
```

Then validate variables without changing the VM:

```bash
ansible-playbook playbooks/validate.yml --ask-vault-pass
```

Fix every validation error before continuing. The validation rejects placeholder domains, example
emails, weak secrets, floating versions, and enabled registration with an empty allowlist.

Deploy:

```bash
ansible-playbook playbooks/site.yml --ask-vault-pass
```

The first run can take several minutes. Ansible installs Docker from Docker's Ubuntu repository,
checks out the exact tag under `/opt/chooseyourtube`, writes a root-only environment file, pulls the
matching images, runs database migrations, starts Caddy and the application, installs systemd and
the backup timer, and checks internal and public health.

Do not interrupt migrations. If the playbook fails, read the failed task and rerun the same command
after correcting the cause; the playbooks are designed to converge safely. Do not bypass preflight
with `chooseyourtube_allow_low_resource` unless the resource risk is understood.

Run the independent health playbook after the deployment finishes:

```bash
ansible-playbook playbooks/health.yml --ask-vault-pass
curl --fail --silent --show-error https://APP_DOMAIN/api/meta
```

Replace `APP_DOMAIN` with the real hostname. Also open `https://APP_DOMAIN` in Safari or Chrome and
verify that it redirects only within the same HTTPS hostname and shows a valid certificate.

**Checkpoint:** `site.yml` and `health.yml` pass, the browser reports a valid certificate, and no
application service is exposed on its internal ports.

## 9. Register and log in from the Mac

Registration is application authentication; it is separate from the Oracle `ubuntu` SSH account.

1. On the Mac, open `https://APP_DOMAIN/register` in Safari or Chrome.
2. Enter the exact address listed under `chooseyourtube_registration_allowlist`. Matching is
   case-insensitive, but using the same spelling avoids confusion.
3. Create a unique, strong password and save it in the Mac's password manager. Do not reuse the SSH
   key passphrase, Google password, Vault password, or database password.
4. Submit the form. Successful registration redirects to `/login?registered=1`.
5. Log in with the new email and password. Successful login redirects to `/inbox`.
6. Add a channel or perform an import and confirm that the inbox loads data for this account.
7. Open a private browsing window and confirm protected pages redirect to login when no session is
   present.

If registration says the email is not allowed, compare the entered address with `main.yml`, rerun
`site.yml`, and try again. Removing an address from the allowlist prevents a future registration but
does not disable an account that already exists.

### Add another user

On the Mac, add the complete address to the list:

```yaml
chooseyourtube_registration_allowlist:
  - "you@example.com"
  - "second-person@example.com"
```

Apply and verify it:

```bash
ansible-playbook playbooks/site.yml --ask-vault-pass
ansible-playbook playbooks/health.yml --ask-vault-pass
```

That person can now use `/register`. Each user's channels, categories, videos, and watch state are
scoped to that account.

After every intended user has registered, onboarding can be closed without affecting existing login:

```yaml
chooseyourtube_registration_enabled: false
```

Rerun `site.yml`. Turn registration back on and keep a non-empty allowlist when inviting someone new.

## 10. Prove recovery and reboot behavior

Fetch an off-host database backup to the Mac:

```bash
ansible-playbook playbooks/backup_fetch.yml --ask-vault-pass
```

The playbook creates a fresh PostgreSQL custom-format dump, verifies its SHA-256 before and after
transfer, and stores it below `deploy/ansible/backups/<inventory-host>/`. Copy important backups to
encrypted storage that is independent of both the VM and this working copy.

Then reboot from the Mac:

```bash
ssh -i /Users/you/.ssh/chooseyourtube_oracle ubuntu@VM_PUBLIC_IP sudo reboot
```

The SSH connection will close. Wait for the instance to return, then run:

```bash
ansible-playbook playbooks/health.yml --ask-vault-pass
```

Log in through the browser again and confirm the account and data remain present. A deployment is not
finished until both an off-host backup and a reboot recovery check have succeeded.

Restore is destructive and replaces the production database. Use the guarded restore playbook only
with an identified dump and an explicit confirmation:

```bash
ansible-playbook playbooks/restore.yml --ask-vault-pass \
  -e restore_confirm=RESTORE \
  -e restore_source=/absolute/path/to/chooseyourtube.dump
```

Prefer testing restore on a separate instance before relying on it in an emergency.

## 11. Normal operations

Run these from the Mac's `deploy/ansible` directory:

```bash
# Health and public reachability
ansible-playbook playbooks/health.yml --ask-vault-pass

# Apply an allowlist or configuration change
ansible-playbook playbooks/site.yml --check --diff --ask-vault-pass
ansible-playbook playbooks/site.yml --ask-vault-pass

# Fetch a verified off-host backup
ansible-playbook playbooks/backup_fetch.yml --ask-vault-pass
```

For an upgrade, read its migration notes, confirm matching Git and image tags exist, change
`chooseyourtube_version`, preview with `--check --diff`, and rerun `site.yml`. Ansible creates a backup
before a version change. It does not automatically reverse a database migration.

For host-level inspection:

```bash
ssh -i /Users/you/.ssh/chooseyourtube_oracle ubuntu@VM_PUBLIC_IP
sudo systemctl status chooseyourtube
sudo systemctl list-timers chooseyourtube-backup.timer
sudo journalctl -u chooseyourtube --since "30 minutes ago"
cd /opt/chooseyourtube
sudo make oracle-health
sudo make oracle-logs
```

Do not manually edit `/opt/chooseyourtube/.env`; Ansible is authoritative and will overwrite it.

## 12. Troubleshooting

| Symptom | Most likely checks |
| --- | --- |
| SSH times out | Update the NSG port-22 source to the Mac's current public IP; verify public subnet, reserved IP, route, and VNIC NSG attachment. |
| SSH warns that the host key changed | Stop. Confirm the reserved IP was not reassigned and compare the OCI-console fingerprint before removing any `known_hosts` entry. |
| `ansible ... -m ping` fails | Test the equivalent direct SSH command; verify `ansible_user`, absolute key path, key permissions, and host fingerprint. |
| Variable validation fails | Replace every example value; ensure registration has at least one complete allowed email and Vault is decrypted with the right password. |
| Git checkout fails on the VM | Confirm the exact `vX.Y.Z` tag exists and the repository is public; current automation does not install a private-repository deploy key. |
| Image pull says unauthorized | Make both GHCR packages public or add a read-only package username/token pair to Vault. |
| Image tag is missing | Wait for both GitHub Actions image jobs and use the version without a leading `v` in `main.yml`. |
| HTTPS or certificate issuance fails | Confirm DNS resolves exactly to the reserved IP and that TCP 80/443 are allowed by security lists, NSG, and any host firewall. |
| Registration is disabled | Set `chooseyourtube_registration_enabled: true`, retain a non-empty allowlist, and rerun `site.yml`. |
| Email is not allowed | Add the complete email to the allowlist and rerun `site.yml`; wildcards are intentionally unsupported. |
| Login fails after successful registration | Use `/login`, check the saved email/password, then inspect application logs without printing the production environment. |
| The host is under pressure | Inspect `free -h`, `df -h`, and `sudo docker stats`; resize the shape or boot volume rather than merely bypassing preflight. |

Never paste the Vault contents, `.env`, API key, database password, auth secret, session cookies, or
private SSH key into an issue or support message. Sanitize logs before sharing them.

## Completion checklist

- [ ] The production commit is tagged and both exact GHCR image tags exist for the VM architecture.
- [ ] The OCI instance runs Ubuntu 24.04 in a public subnet with a reserved public IP.
- [ ] The NSG exposes only public TCP 80/443 and trusted-source TCP 22.
- [ ] DNS `A` resolves the application hostname to the reserved public IP; there is no stray `AAAA`.
- [ ] The YouTube API key is restricted to the Oracle IP and YouTube Data API v3.
- [ ] Inventory and encrypted Vault are backed up; no production files or secrets are tracked by Git.
- [ ] Ansible validation, deployment, and health playbooks pass.
- [ ] HTTPS has a valid certificate and internal service ports are not public.
- [ ] The allowlisted account registers, logs in, reaches `/inbox`, and retains data after a reboot.
- [ ] An off-host, checksum-verified database backup exists.
- [ ] The Vault password, SSH key, DNS access, OCI access, GitHub access, and Google project ownership
      are recorded in the operator's password manager or recovery plan.

# Security policy

## Supported versions

Security fixes are provided for the latest `1.x` release and the current `main` branch.

## Reporting a vulnerability

Please use GitHub's **Report a vulnerability** private advisory flow for this repository. Do not open a
public issue containing an authentication bypass, credential exposure, cross-user data access, remote
code execution or another exploitable security detail.

Include the affected version, deployment mode, reproduction steps, impact and any suggested mitigation.
You should receive an acknowledgement within seven days. A fix and disclosure timeline will be agreed
after the report is reproduced.

## Deployment responsibility

Self-hosters are responsible for keeping dependencies and container images updated, restricting CORS,
using a unique 32+ character `AUTH_SECRET`, protecting database/Redis access, securing backups and
monitoring YouTube quota. Never expose `.env`, Google credentials, database URLs or maintenance secrets
to the frontend.

See [Deployment](docs/deployment.md) for production configuration and rollback guidance.

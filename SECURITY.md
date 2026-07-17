# Security policy

## Supported versions

Security fixes are provided for the latest `1.x` release and the current `main` branch.

## Report a vulnerability

Use GitHub's private **Report a vulnerability** advisory flow for this repository. Do not open a
public issue for an authentication bypass, credential disclosure, cross-user data access, remote code
execution, or another exploitable weakness.

Include:

- the affected version and deployment mode;
- the required configuration or account state;
- reproducible steps or a minimal proof of concept;
- the expected and observed behavior;
- the likely impact;
- a suggested mitigation, if available.

An acknowledgement should arrive within seven days. A remediation and disclosure schedule will be
agreed after the report is reproduced.

## Self-hosting responsibilities

Administrators are responsible for:

- applying dependency and container updates;
- using HTTPS and a unique `AUTH_SECRET` of at least 32 characters;
- restricting FastAPI CORS to the intended frontend origin;
- keeping PostgreSQL and Redis off the public internet;
- protecting `.env`, OAuth credentials, database URLs, API keys, cron secrets, and backups;
- monitoring YouTube API quota and application health;
- testing backups and retaining copies away from the application host.

Access and refresh tokens are stored in HTTP-only cookies at the SvelteKit boundary. Google OAuth
tokens and uploaded Takeout files are not retained after subscription discovery. These application
controls do not replace host, network, TLS, and backup security.

See [Deployment and self-hosting](docs/deployment.md#public-deployment) for production guidance.

# ChooseYourTube documentation

Start with the repository [README](../README.md) for a product overview and Docker quick start.

## Run ChooseYourTube

- [Deployment and self-hosting](deployment.md): production configuration, Docker, backups, upgrades,
  rollback, troubleshooting, and hosted-demo operations.
- [Oracle Cloud VM deployment](oracle-vm.md): Ubuntu host setup, HTTPS, systemd, resource limits,
  and scheduled backups.
- [Frontend development](../frontend/README.md): SvelteKit setup, build targets, API types, and tests.
- [Backend development](../backend/README.md): FastAPI setup, workers, migrations, and tests.

## Understand the system

- [Architecture](architecture.md): component boundaries, request flow, synchronization, ownership,
  and deployment topologies.
- [Engineering decisions](engineering-decisions.md): the reasons behind the main design choices and
  their costs.
- [Accessibility](accessibility.md): WCAG target, test evidence, limitations, and manual audit status.

## Contribute and release

- [Contributing](../CONTRIBUTING.md): project direction, development workflow, and pull request checks.
- [Frontend UI guidelines](frontend-ui-guidelines.md): component, form, feedback, and interaction
  conventions.
- [Manual WCAG checklist](wcag-manual-checklist.md): release checks that require human testing.
- [Security policy](../SECURITY.md): supported versions and private vulnerability reporting.
- [Changelog](../CHANGELOG.md): user-visible changes by release.

## Portfolio and release material

- [Demo and interview guide](demo-script.md)
- [Screenshot capture guide](screenshots/README.md)
- [v1.0.0 release notes](releases/v1.0.0.md)
- [v1.0.0 walkthrough transcript](releases/chooseyourtube-demo-v1.0.0-transcript.md)

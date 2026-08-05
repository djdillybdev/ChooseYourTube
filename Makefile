COMPOSE := docker compose
ENV_FILE := .env

.PHONY: build up down logs ps migrate quickstart test health backup restore release-up release-pull dev-build dev-up dev-down dev-logs dev-ps oracle-config oracle-deploy oracle-health oracle-logs oracle-backup oracle-restore

build:
	$(COMPOSE) --env-file $(ENV_FILE) build

up:
	$(COMPOSE) --env-file $(ENV_FILE) up -d --build

down:
	$(COMPOSE) --env-file $(ENV_FILE) down

logs:
	$(COMPOSE) --env-file $(ENV_FILE) logs -f

ps:
	$(COMPOSE) --env-file $(ENV_FILE) ps

migrate:
	$(COMPOSE) --env-file $(ENV_FILE) run --rm migrate

quickstart:
	./scripts/quickstart.sh

test:
	cd backend && UV_CACHE_DIR=$${TMPDIR:-/tmp}/chooseyourtube-uv-cache uv run ruff check app tests scripts
	cd backend && UV_CACHE_DIR=$${TMPDIR:-/tmp}/chooseyourtube-uv-cache uv run mypy app
	cd backend && UV_CACHE_DIR=$${TMPDIR:-/tmp}/chooseyourtube-uv-cache uv run pytest
	cd frontend && pnpm run api:check && pnpm run check && pnpm run lint && pnpm run test:coverage
	$(COMPOSE) --env-file .env.example config --quiet

health:
	./scripts/health.sh

backup:
	./scripts/backup.sh

restore:
	./scripts/restore.sh

release-pull:
	$(COMPOSE) --env-file $(ENV_FILE) -f compose.yaml -f compose.release.yaml pull

release-up:
	$(COMPOSE) --env-file $(ENV_FILE) -f compose.yaml -f compose.release.yaml up -d

dev-build:
	$(COMPOSE) --env-file $(ENV_FILE) --profile dev build backend-dev worker-dev frontend-dev

dev-up:
	$(COMPOSE) --env-file $(ENV_FILE) --profile dev up -d --build postgres redis migrate backend-dev worker-dev frontend-dev

dev-down:
	$(COMPOSE) --env-file $(ENV_FILE) --profile dev down

dev-logs:
	$(COMPOSE) --env-file $(ENV_FILE) --profile dev logs -f backend-dev worker-dev frontend-dev

dev-ps:
	$(COMPOSE) --env-file $(ENV_FILE) --profile dev ps

oracle-config:
	$(COMPOSE) --env-file $(ENV_FILE) -f compose.yaml -f compose.release.yaml -f deploy/oracle/compose.yaml config --quiet

oracle-deploy:
	./deploy/oracle/bin/deploy.sh

oracle-health:
	./deploy/oracle/bin/health.sh

oracle-logs:
	$(COMPOSE) --env-file $(ENV_FILE) -f compose.yaml -f compose.release.yaml -f deploy/oracle/compose.yaml logs -f

oracle-backup:
	./deploy/oracle/bin/backup.sh

oracle-restore:
	./deploy/oracle/bin/restore.sh

COMPOSE := docker compose
ENV_FILE := .env

.PHONY: build up down logs ps migrate dev-build dev-up dev-down dev-logs dev-ps

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

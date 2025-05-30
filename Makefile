# Development environment configuration
.EXPORT_ALL_VARIABLES:

SHELL := /bin/bash
.DEFAULT_GOAL := help

# Color codes
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Project settings
PROJECT_NAME := mcp_server
PYTHON_VERSION := 3.12
DOCKER_COMPOSE := docker-compose -f docker-compose.dev.yml

# Function to echo in color
define colorecho
	@echo -e "${BLUE}[$$(date +%H:%M:%S)]${NC} ${1}${2}${NC}"
endef

# Function to check if docker is running
define check_docker
	@if ! docker info > /dev/null 2>&1; then \
		echo -e "${RED}Error: Docker is not running${NC}" >&2; \
		exit 1; \
	fi
endef

.PHONY: help
help: ## Show this help message
	@echo -e "Usage: make ${YELLOW}<target>${NC}"
	@echo -e "${BLUE}Available targets:${NC}"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  ${YELLOW}%-20s${NC} %s\n", $$1, $$2}'

# ====================
# Development Environment
# ====================

.PHONY: setup
setup: ## Initial setup of development environment
	$(call colorecho, "Setting up development environment...")
	@./packages/mcp_server/scripts/setup_dev.sh

.PHONY: up
up: ## Start development environment
	$(call check_docker)
	$(call colorecho, "Starting development environment...")
	@mkdir -p logs
	$(DOCKER_COMPOSE) up --build -d
	$(call colorecho, "${GREEN}Development environment is ready!")
	@echo -e "Access points:"
	@echo -e "  API: ${BLUE}http://localhost:8000${NC}"
	@echo -e "  PgAdmin: ${BLUE}http://localhost:5050${NC}"
	@echo -e "  MailHog: ${BLUE}http://localhost:8025${NC}"

.PHONY: down
down: ## Stop development environment
	$(call check_docker)
	$(call colorecho, "Stopping development environment...")
	$(DOCKER_COMPOSE) down

.PHONY: restart
restart: down up ## Restart development environment

.PHONY: clean
clean: ## Clean up development environment (including volumes)
	$(call check_docker)
	$(call colorecho, "Cleaning up development environment...")
	$(DOCKER_COMPOSE) down -v --remove-orphans
	@rm -rf logs/* .pytest_cache .coverage

# ====================
# Database Operations
# ====================

.PHONY: db-migrate
db-migrate: ## Run database migrations
	$(call colorecho, "Running database migrations...")
	$(DOCKER_COMPOSE) exec mcp_server poetry run alembic upgrade head

.PHONY: db-rollback
db-rollback: ## Rollback last database migration
	$(call colorecho, "Rolling back last migration...")
	$(DOCKER_COMPOSE) exec mcp_server poetry run alembic downgrade -1

.PHONY: db-reset
db-reset: ## Reset database to clean state
	$(call colorecho, "Resetting database...")
	$(DOCKER_COMPOSE) exec postgres dropdb -U mcp --if-exists mcp_dev
	$(DOCKER_COMPOSE) exec postgres createdb -U mcp mcp_dev
	@make db-migrate

.PHONY: db-shell
db-shell: ## Open PostgreSQL shell
	$(DOCKER_COMPOSE) exec postgres psql -U mcp -d mcp_dev

# ====================
# Testing
# ====================

.PHONY: test
test: ## Run tests
	$(call colorecho, "Running tests...")
	$(DOCKER_COMPOSE) exec mcp_server poetry run pytest -v --cov=mcp_server tests/

.PHONY: test-watch
test-watch: ## Run tests in watch mode
	$(call colorecho, "Running tests in watch mode...")
	$(DOCKER_COMPOSE) exec mcp_server poetry run ptw --runner "pytest -v --cov=mcp_server tests/"

# ====================
# Code Quality
# ====================

.PHONY: format
format: ## Format code
	$(call colorecho, "Formatting code...")
	$(DOCKER_COMPOSE) exec mcp_server poetry run black mcp_server tests
	$(DOCKER_COMPOSE) exec mcp_server poetry run isort mcp_server tests

.PHONY: lint
lint: ## Run linters
	$(call colorecho, "Running linters...")
	$(DOCKER_COMPOSE) exec mcp_server poetry run flake8 mcp_server tests
	$(DOCKER_COMPOSE) exec mcp_server poetry run mypy mcp_server
	$(DOCKER_COMPOSE) exec mcp_server poetry run black --check mcp_server tests
	$(DOCKER_COMPOSE) exec mcp_server poetry run isort --check-only mcp_server tests

.PHONY: check
check: format lint test ## Run all code quality checks

# ====================
# Documentation
# ====================

.PHONY: docs
docs: ## Generate documentation
	$(call colorecho, "Generating documentation...")
	$(DOCKER_COMPOSE) exec mcp_server poetry run sphinx-build -b html docs/source docs/build

.PHONY: docs-serve
docs-serve: docs ## Serve documentation locally
	$(call colorecho, "Serving documentation at http://localhost:8080")
	@cd docs/build && python3 -m http.server 8080

# ====================
# Utilities
# ====================

.PHONY: shell
shell: ## Open shell in mcp_server container
	$(DOCKER_COMPOSE) exec mcp_server /bin/bash

.PHONY: logs
logs: ## View logs
	$(DOCKER_COMPOSE) logs -f

.PHONY: status
status: ## Show status of all services
	$(DOCKER_COMPOSE) ps

.PHONY: redis-cli
redis-cli: ## Open Redis CLI
	$(DOCKER_COMPOSE) exec redis redis-cli

# ====================
# Production
# ====================

.PHONY: build
build: ## Build production image
	$(call colorecho, "Building production image...")
	docker build -t mcp_server:latest -f packages/mcp_server/Dockerfile packages/mcp_server

.PHONY: deploy
deploy: ## Deploy to production (customize as needed)
	$(call colorecho, "${YELLOW}Warning: Deploy command needs to be customized${NC}")
	@echo "Add your deployment commands here"


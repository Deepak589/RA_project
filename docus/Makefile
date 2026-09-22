# RA App — Developer workflow targets
# All commands run through Docker so the test environment never disagrees
# with the runtime environment. No more "works on my host shell" bugs.

# ---- Config ----------------------------------------------------------------
# Override on the command line if your service names differ:
#   make test API_SERVICE=backend
API_SERVICE ?= api
DB_SERVICE  ?= db
COMPOSE     ?= docker compose

# Pytest args you can override:
#   make test PYTEST_ARGS="-x -k recommendation"
PYTEST_ARGS ?= tests/ -v

# ---- Meta ------------------------------------------------------------------
.PHONY: help up down restart logs ps shell db-shell \
        test test-fast test-cov test-file \
        migrate migrate-down migration \
        lint format \
        frontend-build frontend-dev frontend-install \
        smoke verify clean

help:  ## Show this help
	@echo "RA App — make targets"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---- Stack lifecycle -------------------------------------------------------
up:  ## Start all services in the background (api + db only)
	$(COMPOSE) up -d

up-admin:  ## Start full stack including pgAdmin (http://localhost:5050)
	$(COMPOSE) --profile admin up -d

down:  ## Stop and remove all containers
	$(COMPOSE) down

restart:  ## Restart the API service (use after backend code changes if not auto-reloaded)
	$(COMPOSE) restart $(API_SERVICE)

logs:  ## Tail logs from the API service
	$(COMPOSE) logs -f $(API_SERVICE)

ps:  ## Show running services
	$(COMPOSE) ps

shell:  ## Open a bash shell in the API container
	$(COMPOSE) exec $(API_SERVICE) bash

db-shell:  ## Open psql in the database container
	$(COMPOSE) exec $(DB_SERVICE) psql -U postgres

# ---- Testing (the whole point of this Makefile) ----------------------------
test:  ## Run the full backend test suite inside the API container
	$(COMPOSE) exec -T $(API_SERVICE) pytest $(PYTEST_ARGS)

test-fast:  ## Run tests with -x (stop on first failure) — for tight feedback loops
	$(COMPOSE) exec -T $(API_SERVICE) pytest -x tests/

test-cov:  ## Run tests with coverage report
	$(COMPOSE) exec -T $(API_SERVICE) pytest --cov=app --cov-report=term-missing tests/

test-file:  ## Run a specific test file: make test-file FILE=tests/services/test_rule_engine.py
	@if [ -z "$(FILE)" ]; then echo "Usage: make test-file FILE=tests/path/to/test.py"; exit 1; fi
	$(COMPOSE) exec -T $(API_SERVICE) pytest -v $(FILE)

# ---- Database / migrations -------------------------------------------------
migrate:  ## Apply all pending Alembic migrations
	$(COMPOSE) exec -T $(API_SERVICE) alembic upgrade head

migrate-down:  ## Roll back the last migration
	$(COMPOSE) exec -T $(API_SERVICE) alembic downgrade -1

migration:  ## Create a new Alembic revision: make migration MSG="add user role"
	@if [ -z "$(MSG)" ]; then echo "Usage: make migration MSG=\"description\""; exit 1; fi
	$(COMPOSE) exec -T $(API_SERVICE) alembic revision --autogenerate -m "$(MSG)"

# ---- Code quality ----------------------------------------------------------
lint:  ## Run ruff/flake8 inside the API container (adjust if you use a different linter)
	$(COMPOSE) exec -T $(API_SERVICE) ruff check app/ tests/ || true

format:  ## Run black formatter inside the API container
	$(COMPOSE) exec -T $(API_SERVICE) black app/ tests/ || true

# ---- Frontend (runs on host, since Vite usually does) ----------------------
frontend-install:  ## Install frontend dependencies
	cd frontend && npm install

frontend-build:  ## Build the production frontend bundle
	cd frontend && npm run build

frontend-dev:  ## Start the Vite dev server
	cd frontend && npm run dev

# ---- Verification helpers --------------------------------------------------
smoke:  ## Run the Week 5/6 smoke script inside the API container
	$(COMPOSE) exec -T $(API_SERVICE) python scripts/week5_smoke.py

verify:  ## Run the full verification chain: migrate → test → frontend build
	@echo "==> Running migrations..."
	@$(MAKE) migrate
	@echo "==> Running backend test suite..."
	@$(MAKE) test
	@echo "==> Building frontend..."
	@$(MAKE) frontend-build
	@echo "==> All verification steps passed ✅"

# ---- Cleanup ---------------------------------------------------------------
clean:  ## Remove build artifacts and __pycache__ directories
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "pytest-cache-files-*" -exec rm -rf {} + 2>/dev/null || true
	rm -rf frontend/dist frontend/node_modules/.vite 2>/dev/null || true

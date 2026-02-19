.PHONY: help dev dev-db stop clean-db logs test lint typecheck qa

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

# ── Docker ──────────────────────────────────────────────
dev: ## Start all services (DB + Redis)
	docker compose up -d

dev-db: ## Start only database services (QuestDB + PostgreSQL)
	docker compose up -d questdb postgres

stop: ## Stop all services
	docker compose down

clean-db: ## Stop and remove all volumes (DESTROYS DATA)
	docker compose down -v

logs: ## Tail logs from all services
	docker compose logs -f

# ── QA ──────────────────────────────────────────────────
test: ## Run tests
	uv run pytest tests/ --no-header -q

lint: ## Run linter
	uv run ruff check src/

format: ## Run formatter
	uv run ruff format src/

typecheck: ## Run type checker
	uv run mypy src/auronai/

qa: lint typecheck test ## Run full QA (lint + typecheck + tests)

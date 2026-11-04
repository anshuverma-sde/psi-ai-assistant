API_DIR := apps/api
WEB_DIR := apps/web
PY := $(API_DIR)/.venv/bin/python
API_PORT ?= 8000
WEB_PORT ?= 3000

.PHONY: help setup db migrate api web build pdfs seed eval test lint openapi demo

help:  ## Show available commands
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

setup:  ## Install backend (uv) + frontend (pnpm) dependencies, create per-app env files
	@test -f $(API_DIR)/.env || cp $(API_DIR)/.env.example $(API_DIR)/.env
	@test -f $(WEB_DIR)/.env.local || cp $(WEB_DIR)/.env.example $(WEB_DIR)/.env.local
	cd $(API_DIR) && uv venv --python 3.12 && uv pip install -e ".[dev]"
	cd $(WEB_DIR) && pnpm install

db:  ## Start Postgres + pgvector (docker)
	docker compose up -d db

migrate:  ## Apply database migrations
	cd $(API_DIR) && .venv/bin/alembic upgrade head

api:  ## Run the FastAPI backend (http://localhost:$(API_PORT))
	cd $(API_DIR) && .venv/bin/uvicorn app.main:app --reload --port $(API_PORT)

web:  ## Run the Next.js frontend (http://localhost:$(WEB_PORT))
	cd $(WEB_DIR) && WEB_PORT=$(WEB_PORT) pnpm dev

build:  ## Production build of the frontend
	cd $(WEB_DIR) && pnpm build

pdfs:  ## Regenerate sample PDFs from samples/source/*.md
	$(PY) samples/scripts/generate_pdfs.py

seed:  ## Create the 2 demo organizations and upload their PDFs (API must be running)
	$(PY) samples/scripts/seed.py --api http://localhost:$(API_PORT)

eval:  ## Run the 17 test questions against the running API
	$(PY) samples/scripts/run_eval.py --api http://localhost:$(API_PORT)

test:  ## Run backend unit + e2e tests (uses the psi_test database)
	cd $(API_DIR) && .venv/bin/pytest -q

lint:  ## Lint backend + typecheck/lint frontend
	cd $(API_DIR) && .venv/bin/ruff check app tests
	cd $(WEB_DIR) && pnpm typecheck && pnpm lint

openapi:  ## Export OpenAPI + regenerate frontend API types
	$(PY) $(API_DIR)/scripts/export_openapi.py
	cd $(WEB_DIR) && pnpm gen:api

demo:  ## Build demo/external-site.local.html with seeded tokens and serve it on :5500
	node demo/fill-tokens.mjs http://localhost:$(WEB_PORT)
	python3 -m http.server 5500 --directory demo

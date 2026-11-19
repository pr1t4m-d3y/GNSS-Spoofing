PYTHON ?= python3
RUN_PY = PYTHONPATH=src $(PYTHON)

.DEFAULT_GOAL := help
.PHONY: help install install-dev train eval compare bench bench-http test lint typecheck format up down dev-api dev-web budget deploy smoke teardown

help: ## List targets
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-12s %s\n", $$1, $$2}'

install: ## Install runtime dependencies
	$(PYTHON) -m pip install -r requirements.txt

install-dev: ## Install runtime and development dependencies
	$(PYTHON) -m pip install -r requirements-dev.txt

train: ## Fit the Isolation Forest on data/train.xls and write models/gnss_iforest.pkl + manifest
	$(RUN_PY) -m gnss_shield.train --data data/train.xls --out models/gnss_iforest.pkl

eval: ## Run the evaluation protocol and write evals/results/RESULTS.md
	$(RUN_PY) evals/run.py

compare: ## Isolation Forest vs XGBoost on real labelled data: make compare DATA="data/labelled/a.csv ..."
	$(RUN_PY) evals/compare.py --data $(DATA)

bench: ## Measure model size, memory, latency and throughput; write evals/results/EDGE.md
	$(RUN_PY) evals/bench.py

bench-http: ## Measure end-to-end HTTP latency: make bench-http URL=https://<service-url>
	$(RUN_PY) evals/bench_http.py --base-url $(or $(URL),http://localhost:8000)

test: ## Run the test suite with coverage
	$(RUN_PY) -m pytest --cov --cov-report=term-missing

lint: ## Lint with ruff
	$(PYTHON) -m ruff check .

typecheck: ## Type-check with mypy
	$(PYTHON) -m mypy

format: ## Format with ruff
	$(PYTHON) -m ruff format .

.env:
	cp .env.example .env

up: .env ## Build and start the API (:8000) and dashboard (:3000) with Docker Compose
	docker compose up --build

down: ## Stop the Docker Compose stack
	docker compose down

dev-api: ## Run the API with auto-reload (needs install; auth off unless GNSS_API_KEY is set)
	GNSS_AUTH_DISABLED=$${GNSS_AUTH_DISABLED:-true} PYTHONPATH=src $(PYTHON) -m uvicorn gnss_shield.api:app --reload --port 8000

dev-web: ## Run the dashboard dev server on :3000 against the local API
	cd frontend && npm ci && BACKEND_URL=http://localhost:8000 npm run dev

budget: ## Create a Cloud Billing budget alert (needs BILLING_ACCOUNT_ID, GCP_PROJECT, BUDGET_AMOUNT)
	bash deploy/budget.sh

deploy: ## Deploy API and dashboard to Cloud Run (needs GCP_PROJECT, GCP_REGION)
	bash deploy/deploy.sh

smoke: ## Check the deployed API (health, readiness, auth, one scored batch)
	bash deploy/smoke_test.sh

teardown: ## Delete the Cloud Run services, secret and service account
	bash deploy/teardown.sh

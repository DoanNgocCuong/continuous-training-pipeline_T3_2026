.PHONY: install install-dev test test-unit lint format pipeline \
        infra-argilla infra-mlflow infra-all infra-down infra-logs infra-ps

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

test:
	pytest tests/ -v --cov=finetune --cov-report=term-missing

test-unit:
	pytest tests/unit/ -v

lint:
	ruff check finetune/ tests/
	mypy finetune/ --ignore-missing-imports

format:
	ruff format finetune/ tests/

# Pipeline commands
collect:
	python -m finetune collect --source $(SOURCE)

label:
	python -m finetune label

build:
	python -m finetune build --version $(VERSION)

train:
	python -m finetune train --config $(CONFIG)

evaluate:
	python -m finetune evaluate

decide:
	python -m finetune decide

pipeline:
	./scripts/run_full_pipeline.sh $(SOURCE) $(CONFIG) $(VERSION)

# ── Docker Infra ──────────────────────────────────────────────────────────

COMPOSE = docker compose -f docker-compose-infra.yml

infra-argilla:
	$(COMPOSE) --profile argilla up -d

infra-mlflow:
	$(COMPOSE) --profile mlflow up -d

infra-all:
	$(COMPOSE) --profile all up -d

infra-down:
	$(COMPOSE) --profile all down

infra-logs:
	$(COMPOSE) --profile all logs -f $(SERVICE)

infra-ps:
	$(COMPOSE) --profile all ps

infra-build:
	$(COMPOSE) build mlflow

include .env
export $(shell sed 's/=.*//' .env)

VENV = .venv

POSTGRES_SERVER=localhost
POSTGRES_PORT=5433
POSTGRES_USER=test
POSTGRES_PASSWORD=test
POSTGRES_DB=test
REDIS_HOST=localhost
REDIS_PORT=6378

.PHONY: test
test:
	pytest $(scope)


.PHONY: format
format:
	ruff check app --fix-only && \
	ruff format app

.PHONY: lint
lint:
	ruff check app --output-format=github && \
	ruff format app --check

.PHONY: type-check
type-check:
	mypy --install-types --non-interactive .

.PHONY: code-check
code-check: format lint type-check

.PHONY: rmpyc
rmpyc:
	find . -name "__pycache__" -type d -exec rm -r {} +

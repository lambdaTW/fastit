.EXPORT_ALL_VARIABLES:
PYTHONPATH = ${PWD}/src

lint:  ## Run linting
	python -m black --check .
	python -m isort -c .
	python -m ruff .
.PHONY: lint

lint-fix:  ## Run autoformatters
	python -m black .
	python -m isort .
.PHONY: lint-fix

pip-tools:  ## Install pip-tools
	pip3 show pip-tools && echo "pip-tools is installed" || (pip3 install -U pip && pip3 install -U pip-tools)
.PHONY: pip-tools

pip-build: pip-tools  ## Recompile all pip packages
	ls requirements/*.in | xargs -n1 pip-compile --resolver=backtracking --strip-extras
.PHONY: pip-build

pip-install: pip-tools  ## Install all pip packages
	pip-sync `ls requirements/*.txt`
.PHONY: pip-install

pip: pip-build pip-install  ## Recompile and install all pip packages
.PHONY: pip

test:  ## Run test only
	pytest .
.PHONY: test

migrate:  ## Migrate DB to head version
	cd src/app/ && python -m alembic upgrade head
.PHONY: migrate

migrations:  ## Make alembic migrations, ex: make migrations msg="create auth tables"
	cd src/app/ && python -m alembic revision --autogenerate -m "$(msg)"
.PHONY: migrations

.DEFAULT_GOAL := help
help: Makefile  ## Show Makefile help
	@echo "Below shows Makefile targets"
	@grep -E '(^[a-zA-Z_-]+:.*?##.*$$)|(^##)' Makefile | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[32m%-30s\033[0m %s\n", $$1, $$2}' | sed -e 's/\[32m##/[33m/'


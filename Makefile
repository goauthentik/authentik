.PHONY: gen dev-reset all clean test web docs

SHELL := /usr/bin/env bash
.SHELLFLAGS += ${SHELLFLAGS} -e -o pipefail
PWD = $(shell pwd)
UID = $(shell id -u)
GID = $(shell id -g)
NPM_VERSION = $(shell python -m scripts.generate_semver)
PY_SOURCES = authentik packages tests scripts lifecycle .github
DOCKER_IMAGE ?= "authentik:test"

GEN_API_TS = gen-ts-api
GEN_API_PY = gen-py-api
GEN_API_GO = gen-go-api

pg_user := $(shell uv run python -m authentik.lib.config postgresql.user 2>/dev/null)
pg_host := $(shell uv run python -m authentik.lib.config postgresql.host 2>/dev/null)
pg_name := $(shell uv run python -m authentik.lib.config postgresql.name 2>/dev/null)
redis_db := $(shell uv run python -m authentik.lib.config redis.db 2>/dev/null)

UNAME := $(shell uname)

# For macOS users, add the libxml2 installed from brew libxmlsec1 to the build path
# to prevent SAML-related tests from failing and ensure correct pip dependency compilation
ifeq ($(UNAME), Darwin)
# Only add for brew users who installed libxmlsec1
	BREW_EXISTS := $(shell command -v brew 2> /dev/null)
	ifdef BREW_EXISTS
		LIBXML2_EXISTS := $(shell brew list libxml2 2> /dev/null)
		ifdef LIBXML2_EXISTS
			BREW_LDFLAGS := -L$(shell brew --prefix libxml2)/lib $(LDFLAGS)
			BREW_CPPFLAGS := -I$(shell brew --prefix libxml2)/include $(CPPFLAGS)
			BREW_PKG_CONFIG_PATH := $(shell brew --prefix libxml2)/lib/pkgconfig:$(PKG_CONFIG_PATH)
		endif
	endif
endif

all: lint-fix lint gen web test  ## Lint, build, and test everything

HELP_WIDTH := $(shell grep -h '^[a-z][^ ]*:.*\#\#' $(MAKEFILE_LIST) 2>/dev/null | \
	cut -d':' -f1 | awk '{printf "%d\n", length}' | sort -rn | head -1)

help:  ## Show this help
	@echo "\nSpecify a command. The choices are:\n"
	@grep -Eh '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[0;36m%-$(HELP_WIDTH)s  \033[m %s\n", $$1, $$2}' | \
		sort
	@echo ""

go-test:
	go test -timeout 0 -v -race -cover ./...

test: ## Run the server tests and produce a coverage report (locally)
	uv run coverage run manage.py test --keepdb authentik
	uv run coverage html
	uv run coverage report

lint-fix: lint-codespell  ## Lint and automatically fix errors in the python source code. Reports spelling errors.
	uv run black $(PY_SOURCES)
	uv run ruff check --fix $(PY_SOURCES)

lint-codespell:  ## Reports spelling errors.
	uv run codespell -w

lint: ## Lint the python and golang sources
	uv run bandit -c pyproject.toml -r $(PY_SOURCES)
	golangci-lint run -v

core-install:
ifdef LIBXML2_EXISTS
# Clear cache to ensure fresh compilation
	uv cache clean
# Force compilation from source for lxml and xmlsec with correct environment
	LDFLAGS="$(BREW_LDFLAGS)" CPPFLAGS="$(BREW_CPPFLAGS)" PKG_CONFIG_PATH="$(BREW_PKG_CONFIG_PATH)" uv sync --frozen --reinstall-package lxml --reinstall-package xmlsec --no-binary-package lxml --no-binary-package xmlsec
else
	uv sync --frozen
endif

migrate: ## Run the Authentik Django server's migrations
	uv run python -m lifecycle.migrate

i18n-extract: core-i18n-extract web-i18n-extract  ## Extract strings that require translation into files to send to a translation service

aws-cfn:
	cd lifecycle/aws && npm i && uv run npm run aws-cfn

run-server:  ## Run the main authentik server process
	uv run ak server

run-worker:  ## Run the main authentik worker process
	uv run ak worker

core-i18n-extract:
	uv run ak makemessages \
		--add-location file \
		--no-obsolete \
		--ignore web \
		--ignore internal \
		--ignore ${GEN_API_TS} \
		--ignore ${GEN_API_GO} \
		--ignore website \
		-l en

install: node-install docs-install core-install  ## Install all requires dependencies for `node`, `docs` and `core`

dev-drop-db:
	dropdb -U ${pg_user} -h ${pg_host} ${pg_name} || true
	# Also remove the test-db if it exists
	dropdb -U ${pg_user} -h ${pg_host} test_${pg_name} || true
	redis-cli -n ${redis_db} flushall

dev-create-db:
	createdb -U ${pg_user} -h ${pg_host} ${pg_name}

dev-reset: dev-drop-db dev-create-db migrate  ## Drop and restore the Authentik PostgreSQL instance to a "fresh install" state.

update-test-mmdb:  ## Update test GeoIP and ASN Databases
	curl -L https://raw.githubusercontent.com/maxmind/MaxMind-DB/refs/heads/main/test-data/GeoLite2-ASN-Test.mmdb -o ${PWD}/tests/GeoLite2-ASN-Test.mmdb
	curl -L https://raw.githubusercontent.com/maxmind/MaxMind-DB/refs/heads/main/test-data/GeoLite2-City-Test.mmdb -o ${PWD}/tests/GeoLite2-City-Test.mmdb

bump:  ## Bump authentik version. Usage: make bump version=20xx.xx.xx
ifndef version
	$(error Usage: make bump version=20xx.xx.xx )
endif
	sed -i 's/^version = ".*"/version = "$(version)"/' pyproject.toml
	sed -i 's/^VERSION = ".*"/VERSION = "$(version)"/' authentik/__init__.py
	$(MAKE) gen-build gen-compose aws-cfn
	npm version --no-git-tag-version --allow-same-version $(version)
	cd ${PWD}/web && npm version --no-git-tag-version --allow-same-version $(version)
	echo -n $(version) > ${PWD}/internal/constants/VERSION

#########################
## API Schema
#########################

gen-build:  ## Extract the schema from the database
	AUTHENTIK_DEBUG=true \
		AUTHENTIK_TENANTS__ENABLED=true \
		AUTHENTIK_OUTPOSTS__DISABLE_EMBEDDED_OUTPOST=true \
		uv run ak make_blueprint_schema --file blueprints/schema.json
	AUTHENTIK_DEBUG=true \
		AUTHENTIK_TENANTS__ENABLED=true \
		AUTHENTIK_OUTPOSTS__DISABLE_EMBEDDED_OUTPOST=true \
		uv run ak spectacular --file schema.yml

gen-compose:
	uv run scripts/generate_docker_compose.py

gen-changelog:  ## (Release) generate the changelog based from the commits since the last tag
	git log --pretty=format:" - %s" $(shell git describe --tags $(shell git rev-list --tags --max-count=1))...$(shell git branch --show-current) | sort > changelog.md
	npx prettier --write changelog.md

gen-diff:  ## (Release) generate the changelog diff between the current schema and the last tag
	git show $(shell git describe --tags $(shell git rev-list --tags --max-count=1)):schema.yml > old_schema.yml
	docker run \
		--rm -v ${PWD}:/local \
		--user ${UID}:${GID} \
		docker.io/openapitools/openapi-diff:2.1.0-beta.8 \
		--markdown /local/diff.md \
		/local/old_schema.yml /local/schema.yml
	rm old_schema.yml
	sed -i 's/{/&#123;/g' diff.md
	sed -i 's/}/&#125;/g' diff.md
	npx prettier --write diff.md

gen-clean-ts:  ## Remove generated API client for TypeScript
	rm -rf ${PWD}/${GEN_API_TS}/
	rm -rf ${PWD}/web/node_modules/@goauthentik/api/

gen-clean-go:  ## Remove generated API client for Go
	mkdir -p ${PWD}/${GEN_API_GO}
ifneq ($(wildcard ${PWD}/${GEN_API_GO}/.*),)
	make -C ${PWD}/${GEN_API_GO} clean
else
	rm -rf ${PWD}/${GEN_API_GO}
endif

gen-clean-py:  ## Remove generated API client for Python
	rm -rf ${PWD}/${GEN_API_PY}/

gen-clean: gen-clean-ts gen-clean-go gen-clean-py  ## Remove generated API clients

gen-client-ts: gen-clean-ts  ## Build and install the authentik API for Typescript into the authentik UI Application
	docker run \
		--rm -v ${PWD}:/local \
		--user ${UID}:${GID} \
		docker.io/openapitools/openapi-generator-cli:v7.15.0 generate \
		-i /local/schema.yml \
		-g typescript-fetch \
		-o /local/${GEN_API_TS} \
		-c /local/scripts/api-ts-config.yaml \
		--additional-properties=npmVersion=${NPM_VERSION} \
		--git-repo-id authentik \
		--git-user-id goauthentik

	cd ${PWD}/${GEN_API_TS} && npm i
	cd ${PWD}/${GEN_API_TS} && npm link
	cd ${PWD}/web && npm link @goauthentik/api

gen-client-py: gen-clean-py ## Build and install the authentik API for Python
	docker run \
		--rm -v ${PWD}:/local \
		--user ${UID}:${GID} \
		docker.io/openapitools/openapi-generator-cli:v7.15.0 generate \
		-i /local/schema.yml \
		-g python \
		-o /local/${GEN_API_PY} \
		-c /local/scripts/api-py-config.yaml \
		--additional-properties=packageVersion=${NPM_VERSION} \
		--git-repo-id authentik \
		--git-user-id goauthentik

gen-client-go: gen-clean-go  ## Build and install the authentik API for Golang
	mkdir -p ${PWD}/${GEN_API_GO}
ifeq ($(wildcard ${PWD}/${GEN_API_GO}/.*),)
	git clone --depth 1 https://github.com/goauthentik/client-go.git ${PWD}/${GEN_API_GO}
else
	cd ${PWD}/${GEN_API_GO} && git pull
endif
	cp ${PWD}/schema.yml ${PWD}/${GEN_API_GO}
	make -C ${PWD}/${GEN_API_GO} build
	go mod edit -replace goauthentik.io/api/v3=./${GEN_API_GO}

gen-dev-config:  ## Generate a local development config file
	uv run scripts/generate_config.py

gen: gen-build gen-client-ts

#########################
## Node.js
#########################

node-install:  ## Install the necessary libraries to build Node.js packages
	npm ci
	npm ci --prefix web

#########################
## Web
#########################

web-build: node-install  ## Build the Authentik UI
	npm run --prefix web build

web: web-lint-fix web-lint web-check-compile  ## Automatically fix formatting issues in the Authentik UI source code, lint the code, and compile it

web-test: ## Run tests for the Authentik UI
	npm run --prefix web test

web-watch:  ## Build and watch the Authentik UI for changes, updating automatically
	npm run --prefix web watch
web-storybook-watch:  ## Build and run the storybook documentation server
	npm run --prefix web storybook

web-lint-fix:
	npm run --prefix web prettier

web-lint:
	npm run --prefix web lint
	npm run --prefix web lit-analyse

web-check-compile:
	npm run --prefix web tsc

web-i18n-extract:
	npm run --prefix web extract-locales

#########################
## Docs
#########################

docs: docs-lint-fix docs-build  ## Automatically fix formatting issues in the Authentik docs source code, lint the code, and compile it

docs-install:
	npm ci --prefix website

docs-lint-fix: lint-codespell
	npm run --prefix website prettier

docs-build:
	npm run --prefix website build

docs-watch:  ## Build and watch the topics documentation
	npm run --prefix website start

integrations: docs-lint-fix integrations-build ## Fix formatting issues in the integrations source code, lint the code, and compile it

integrations-build:
	npm run --prefix website -w integrations build

integrations-watch:  ## Build and watch the Integrations documentation
	npm run --prefix website -w integrations start

docs-api-build:
	npm run --prefix website -w api build

docs-api-watch:  ## Build and watch the API documentation
	npm run --prefix website -w api build:api
	npm run --prefix website -w api start

docs-api-clean: ## Clean generated API documentation
	npm run --prefix website -w api build:api:clean

#########################
## Docker
#########################

docker:  ## Build a docker image of the current source tree
	mkdir -p ${GEN_API_TS}
	DOCKER_BUILDKIT=1 docker build . --progress plain --tag ${DOCKER_IMAGE}

test-docker:
	BUILD=true ${PWD}/scripts/test_docker.sh

#########################
## CI
#########################
# These targets are use by GitHub actions to allow usage of matrix
# which makes the YAML File a lot smaller

ci--meta-debug:
	python -V
	node --version

ci-mypy: ci--meta-debug
	uv run mypy --strict $(PY_SOURCES)

ci-black: ci--meta-debug
	uv run black --check $(PY_SOURCES)

ci-ruff: ci--meta-debug
	uv run ruff check $(PY_SOURCES)

ci-codespell: ci--meta-debug
	uv run codespell -s

ci-bandit: ci--meta-debug
	uv run bandit -r $(PY_SOURCES)

ci-pending-migrations: ci--meta-debug
	uv run ak makemigrations --check

ci-test: ci--meta-debug
	uv run coverage run manage.py test --keepdb --randomly-seed ${CI_TEST_SEED} authentik
	uv run coverage report
	uv run coverage xml

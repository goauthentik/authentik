.PHONY: gen dev-reset all clean test web docs

SHELL := /usr/bin/env bash
.SHELLFLAGS += ${SHELLFLAGS} -e -o pipefail
PWD = $(shell pwd)
UID = $(shell id -u)
GID = $(shell id -g)
NPM_VERSION = $(shell python -m scripts.generate_semver)
PY_SOURCES = authentik packages tests scripts lifecycle .github
DOCKER_IMAGE ?= "authentik:test"

UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
	SED_INPLACE = sed -i ''
else
	SED_INPLACE = sed -i
endif

GEN_API_TS = gen-ts-api
GEN_API_PY = gen-py-api
GEN_API_GO = gen-go-api

BREW_LDFLAGS :=
BREW_CPPFLAGS :=
BREW_PKG_CONFIG_PATH :=

UV := uv

# For macOS users, add the libxml2 installed from brew libxmlsec1 to the build path
# to prevent SAML-related tests from failing and ensure correct pip dependency compilation
ifeq ($(UNAME_S),Darwin)
# Only add for brew users who installed libxmlsec1
	BREW_EXISTS := $(shell command -v brew 2> /dev/null)
	ifdef BREW_EXISTS
		LIBXML2_EXISTS := $(shell brew list libxml2 2> /dev/null)
		ifdef LIBXML2_EXISTS
			_xml_pref := $(shell brew --prefix libxml2)
			BREW_LDFLAGS += -L${_xml_pref}/lib
			BREW_CPPFLAGS += -I${_xml_pref}/include
			BREW_PKG_CONFIG_PATH = ${_xml_pref}/lib/pkgconfig:$(PKG_CONFIG_PATH)
		endif
		KRB5_EXISTS := $(shell brew list krb5 2> /dev/null)
		ifdef KRB5_EXISTS
			_krb5_pref := $(shell brew --prefix krb5)
			BREW_LDFLAGS += -L${_krb5_pref}/lib
			BREW_CPPFLAGS += -I${_krb5_pref}/include
			BREW_PKG_CONFIG_PATH = ${_krb5_pref}/lib/pkgconfig:$(PKG_CONFIG_PATH)
		endif
		UV := LDFLAGS="$(BREW_LDFLAGS)" CPPFLAGS="$(BREW_CPPFLAGS)" PKG_CONFIG_PATH="$(BREW_PKG_CONFIG_PATH)" uv
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
	$(UV) run coverage run manage.py test --keepdb $(or $(filter-out $@,$(MAKECMDGOALS)),authentik)
	$(UV) run coverage html
	$(UV) run coverage report

lint-fix: lint-codespell  ## Lint and automatically fix errors in the python source code. Reports spelling errors.
	$(UV) run black $(PY_SOURCES)
	$(UV) run ruff check --fix $(PY_SOURCES)

lint-codespell:  ## Reports spelling errors.
	$(UV) run codespell -w

lint: ci-bandit ## Lint the python and golang sources
	golangci-lint run -v

core-install:
ifdef ($(BREW_EXISTS))
# Clear cache to ensure fresh compilation
	$(UV) cache clean
# Force compilation from source for lxml and xmlsec with correct environment
	$(UV) sync --frozen --reinstall-package lxml --reinstall-package xmlsec --no-binary-package lxml --no-binary-package xmlsec
else
	$(UV) sync --frozen
endif

migrate: ## Run the Authentik Django server's migrations
	$(UV) run python -m lifecycle.migrate

i18n-extract: core-i18n-extract web-i18n-extract  ## Extract strings that require translation into files to send to a translation service

aws-cfn:
	cd lifecycle/aws && npm i && $(UV) run npm run aws-cfn

run-server:  ## Run the main authentik server process
	$(UV) run ak server

run-worker:  ## Run the main authentik worker process
	$(UV) run ak worker

core-i18n-extract:
	$(UV) run ak makemessages \
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
	$(eval pg_user := $(shell $(UV) run python -m authentik.lib.config postgresql.user 2>/dev/null))
	$(eval pg_host := $(shell $(UV) run python -m authentik.lib.config postgresql.host 2>/dev/null))
	$(eval pg_name := $(shell $(UV) run python -m authentik.lib.config postgresql.name 2>/dev/null))
	dropdb -U ${pg_user} -h ${pg_host} ${pg_name} || true
	# Also remove the test-db if it exists
	dropdb -U ${pg_user} -h ${pg_host} test_${pg_name} || true

dev-create-db:
	$(eval pg_user := $(shell $(UV) run python -m authentik.lib.config postgresql.user 2>/dev/null))
	$(eval pg_host := $(shell $(UV) run python -m authentik.lib.config postgresql.host 2>/dev/null))
	$(eval pg_name := $(shell $(UV) run python -m authentik.lib.config postgresql.name 2>/dev/null))
	createdb -U ${pg_user} -h ${pg_host} ${pg_name}

dev-reset: dev-drop-db dev-create-db migrate  ## Drop and restore the Authentik PostgreSQL instance to a "fresh install" state.

update-test-mmdb:  ## Update test GeoIP and ASN Databases
	curl -L https://raw.githubusercontent.com/maxmind/MaxMind-DB/refs/heads/main/test-data/GeoLite2-ASN-Test.mmdb -o ${PWD}/tests/GeoLite2-ASN-Test.mmdb
	curl -L https://raw.githubusercontent.com/maxmind/MaxMind-DB/refs/heads/main/test-data/GeoLite2-City-Test.mmdb -o ${PWD}/tests/GeoLite2-City-Test.mmdb

bump:  ## Bump authentik version. Usage: make bump version=20xx.xx.xx
ifndef version
	$(error Usage: make bump version=20xx.xx.xx )
endif
	$(SED_INPLACE) 's/^version = ".*"/version = "$(version)"/' pyproject.toml
	$(SED_INPLACE) 's/^VERSION = ".*"/VERSION = "$(version)"/' authentik/__init__.py
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
		$(UV) run ak build_schema

gen-compose:
	$(UV) run scripts/generate_compose.py

gen-changelog:  ## (Release) generate the changelog based from the commits since the last tag
	git log --pretty=format:" - %s" $(shell git describe --tags $(shell git rev-list --tags --max-count=1))...$(shell git branch --show-current) | sort > changelog.md
	npx prettier --write changelog.md

gen-diff:  ## (Release) generate the changelog diff between the current schema and the last tag
	git show $(shell git describe --tags $(shell git rev-list --tags --max-count=1)):schema.yml > schema-old.yml
	docker compose -f scripts/api/compose.yml run --rm --user "${UID}:${GID}" diff \
		--markdown \
		/local/diff.md \
		/local/schema-old.yml \
		/local/schema.yml
	rm schema-old.yml
	$(SED_INPLACE) 's/{/&#123;/g' diff.md
	$(SED_INPLACE) 's/}/&#125;/g' diff.md
	npx prettier --write diff.md

gen-clean-ts:  ## Remove generated API client for TypeScript
	rm -rf ${PWD}/${GEN_API_TS}/
	rm -rf ${PWD}/web/node_modules/@goauthentik/api/

gen-clean-py:  ## Remove generated API client for Python
	rm -rf ${PWD}/${GEN_API_PY}

gen-clean-go:  ## Remove generated API client for Go
	rm -rf ${PWD}/${GEN_API_GO}

gen-clean: gen-clean-ts gen-clean-go gen-clean-py  ## Remove generated API clients

gen-client:
	if [ "$$(git rev-parse --abbrev-ref HEAD | grep -o '^version-')" = "version-" ]; then \
		mkdir -p ${gen_api_path}; \
		git clone --depth 1 https://github.com/goauthentik/client-${gen_api_lang}.git -b $$(git rev-parse --abbrev-ref HEAD) ${gen_api_path} || true; \
	fi
	if [ ! -d ${gen_api_path} ]; then \
		git clone --depth 1 https://github.com/goauthentik/client-${gen_api_lang}.git ${gen_api_path}; \
	fi
	cp ${PWD}/schema.yml ${gen_api_path}
	make -C ${gen_api_path} build version=${NPM_VERSION}

gen-client-ts: gen-clean-ts  ## Build and install the authentik API for Typescript into the authentik UI Application
	docker compose -f scripts/api/compose.yml run --rm --user "${UID}:${GID}" gen \
		generate \
		-i /local/schema.yml \
		-g typescript-fetch \
		-o /local/${GEN_API_TS} \
		-c /local/scripts/api/ts-config.yaml \
		--additional-properties=npmVersion=${NPM_VERSION} \
		--git-repo-id authentik \
		--git-user-id goauthentik

	cd ${PWD}/${GEN_API_TS} && npm i
	cd ${PWD}/${GEN_API_TS} && npm link
	cd ${PWD}/web && npm link @goauthentik/api

gen-client-py: gen-clean-py ## Build and install the authentik API for Python
	$(MAKE) gen-client gen_api_lang=python gen_api_path=${PWD}/${GEN_API_PY}

gen-client-go: gen-clean-go  ## Build and install the authentik API for Golang
	$(MAKE) gen-client gen_api_lang=go gen_api_path=${PWD}/${GEN_API_GO}
	go mod edit -replace goauthentik.io/api/v3=./${GEN_API_GO}

gen-dev-config:  ## Generate a local development config file
	$(UV) run scripts/generate_config.py

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
	DOCKER_BUILDKIT=1 docker build . -f lifecycle/container/Dockerfile --progress plain --tag ${DOCKER_IMAGE}

test-docker:
	BUILD=true ${PWD}/scripts/test_docker.sh

#########################
## CI
#########################
# These targets are use by GitHub actions to allow usage of matrix
# which makes the YAML File a lot smaller

ci--meta-debug:
	$(UV) run python -V
	node --version

ci-mypy: ci--meta-debug
	$(UV) run mypy --strict $(PY_SOURCES)

ci-black: ci--meta-debug
	$(UV) run black --check $(PY_SOURCES)

ci-ruff: ci--meta-debug
	$(UV) run ruff check $(PY_SOURCES)

ci-codespell: ci--meta-debug
	$(UV) run codespell -s

ci-bandit: ci--meta-debug
	$(UV) run bandit -c pyproject.toml -r $(PY_SOURCES) -iii

ci-pending-migrations: ci--meta-debug
	$(UV) run ak makemigrations --check

ci-test: ci--meta-debug
	$(UV) run coverage run manage.py test --keepdb authentik
	$(UV) run coverage report
	$(UV) run coverage xml

.PHONY: gen dev-reset all test web docs core-install i18n-extract gen-locales locales-normalize install bump gen-changelog integrations

SHELL := /usr/bin/env bash
.SHELLFLAGS += ${SHELLFLAGS} -e -o pipefail
PWD = $(shell pwd)
UID = $(shell id -u)
GID = $(shell id -g)
PY_SOURCES = authentik packages tests scripts lifecycle
DOCKER_IMAGE ?= "authentik:test"

UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
	SED_INPLACE = /usr/bin/sed -i ''
else
	SED_INPLACE = sed -i
endif

BREW_LDFLAGS :=
BREW_CPPFLAGS :=
BREW_PKG_CONFIG_PATH :=

CARGO := cargo
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

NPM_VERSION :=
UV_EXISTS := $(shell command -v uv 2> /dev/null)
ifdef UV_EXISTS
	NPM_VERSION := $(shell $(UV) run python -m scripts.generate_semver)
else
	NPM_VERSION = $(shell python -m scripts.generate_semver)
endif

all: lint-fix lint gen web test  ## Lint-fix, lint, generate the schema, generate the client libraries, lint the front end, run the python tests

HELP_WIDTH := $(shell grep -h '^[a-z][^ ]*:.*\#\#' $(MAKEFILE_LIST) 2>/dev/null | \
	cut -d':' -f1 | awk '{printf "%d\n", length}' | sort -rn | head -1)

help:  ## Show this help
	@echo "\nSpecify a command. The choices are:\n"
	@grep -Eh '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[0;36m%-$(HELP_WIDTH)s  \033[m %s\n", $$1, $$2}' | \
		sort
	@echo ""

go-test:  ## Run the golang tests
	go test -timeout 0 -v -race -cover ./...

rust-test:  ## Run the Rust tests
	$(CARGO) nextest run --workspace

test: ## Run the server tests and produce a coverage report (locally). Usage: make test [path]
	$(UV) run coverage run manage.py test --keepdb $(or $(filter-out $@ all,$(MAKECMDGOALS)),authentik)
	$(UV) run coverage combine
	$(UV) run coverage html
	$(UV) run coverage report

lint-fix-rust:  ## Format Rust sources (rustfmt)
	$(CARGO) +nightly fmt --all -- --config-path "${PWD}/.cargo/rustfmt.toml"

lint-fix: lint-fix-rust  ## Format and automatically fix Python (black, ruff) and Rust (rustfmt) sources
	$(UV) run black $(PY_SOURCES)
	$(UV) run ruff check --fix $(PY_SOURCES)

lint-spellcheck:  ## Reports spelling errors.
	npm run lint:spellcheck

lint-catalogs:  ## Reports pnpm catalog pins, and pnpm's own version pin, that drifted between workspaces.
	node ./scripts/node/lint-catalogs.ts

lint-locales:  ## Reports translation files and generated locale lists that drifted from locales.yaml.
	$(UV) run python scripts/locales.py check

lint-check-types:  ## Type-check the repository's Node.js scripts.
	pnpm run build:types

lint: ci-lint-bandit ci-lint-mypy ci-lint-cargo-deny ci-lint-cargo-machete  ## Check Python (bandit, mypy), Go (golangci) and Rust dependencies (cargo deny, machete)
	golangci-lint run -v

core-install:
ifneq ($(BREW_EXISTS),)
# Clear cache to ensure fresh compilation
	$(UV) cache clean
# Force compilation from source for lxml and xmlsec with correct environment
	$(UV) sync --frozen --reinstall-package lxml --reinstall-package xmlsec --no-binary-package lxml --no-binary-package xmlsec
else
	$(UV) sync --frozen
endif

migrate: ## Apply and check system and Django migrations
	$(UV) run python -m lifecycle.migrate

i18n-extract: core-i18n-extract web-i18n-extract  ## Extract strings that require translation into files to send to a translation service

gen-locales:  ## Regenerate lit-localize.json, the web locale loaders, and the Transifex language mapping from locales.yaml
	$(UV) run python scripts/locales.py gen

locales-normalize:  ## Move translation files that Transifex wrote under non-canonical names to their canonical paths
	$(UV) run python scripts/locales.py normalize

aws-cfn: node-install  ## Generate the AWS Cloudformation template
	pnpm --dir lifecycle/aws install
	$(UV) run pnpm --dir lifecycle/aws run aws-cfn

run:  ## Run the main authentik server and worker processes
	$(UV) run ak allinone

run-watch:  ## Run the authentik server and worker, with auto reloading
	watchexec --on-busy-update=restart --stop-signal=SIGINT --exts py,rs --no-meta --notify -- $(UV) run ak allinone

core-i18n-extract:
	$(UV) run python -m manage makemessages \
		--add-location file \
		--no-obsolete \
		--ignore web \
		--ignore internal \
		--ignore packages/client-ts \
		--ignore website \
		-l en

install: node-install web-install core-install  ## Install all required dependencies for `node`, `web` and `core`

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

dev-reset: dev-drop-db dev-create-db migrate  ## Drop and restore the authentik PostgreSQL instance to a "fresh install" state.

make-migrations:  ## Create Django migrations for model changes (pgtrigger-aware)
	$(UV) run ak makemigrations

update-test-mmdb:  ## Update test GeoIP and ASN Databases
	curl \
		-L \
		-o ${PWD}/tests/geoip/GeoLite2-ASN-Test.mmdb \
		https://raw.githubusercontent.com/maxmind/MaxMind-DB/refs/heads/main/test-data/GeoLite2-ASN-Test.mmdb
	curl \
		-L \
		-o ${PWD}/tests/geoip/GeoLite2-City-Test.mmdb \
		https://raw.githubusercontent.com/maxmind/MaxMind-DB/refs/heads/main/test-data/GeoLite2-City-Test.mmdb

bump:  ## Bump authentik version. Usage: make bump version=20xx.xx.xx
ifndef version
	$(error Usage: make bump version=20xx.xx.xx )
endif
	$(eval current_version := $(shell cat ${PWD}/internal/constants/VERSION))
	$(SED_INPLACE) 's/^version = ".*"/version = "$(version)"/' ${PWD}/pyproject.toml
	$(SED_INPLACE) 's/^VERSION = ".*"/VERSION = "$(version)"/' ${PWD}/authentik/__init__.py
	$(SED_INPLACE) "s/version = \"${current_version}\"/version = \"$(version)\"/" ${PWD}/Cargo.toml ${PWD}/Cargo.lock
	$(MAKE) gen-build gen-compose aws-cfn
	$(SED_INPLACE) "s/\"${current_version}\"/\"$(version)\"/" ${PWD}/package.json ${PWD}/web/package.json
	echo -n $(version) > ${PWD}/internal/constants/VERSION

#########################
## API Schema
#########################

gen-build:  ## Generate schema.yml and blueprints/schema.json from Django model definitions
	AUTHENTIK_DEBUG=true \
		AUTHENTIK_OUTPOSTS__DISABLE_EMBEDDED_OUTPOST=true \
		$(UV) run python -m manage build_schema

gen-compose:
	$(UV) run scripts/generate_compose.py

gen-changelog:  ## (Release) generate the changelog based from the commits since the last version
# These are best-effort guesses based on commit messages
	$(eval last_version := $(shell git tag --list 'version/*' --sort 'version:refname' | grep -vE 'rc[0-9]+$$' | tail -1))
	$(eval current_commit := $(shell git rev-parse HEAD))
	git log --pretty=format:"- %s" $(shell git merge-base ${last_version} ${current_commit})...${current_commit} > merged_to_current
	git log --pretty=format:"- %s" $(shell git merge-base ${last_version} ${current_commit})...${last_version} > merged_to_last
	{ grep -Eo 'cherry-pick (#[0-9]+)' merged_to_last || true; } | cut -d ' ' -f 2 | sed 's/.*/(&)$$/' > cherry_picked_to_last
	grep -vf cherry_picked_to_last merged_to_current | grep -vE '^- (ci:|website)' | sort > changelog.md
	rm merged_to_current
	rm merged_to_last
	rm cherry_picked_to_last
	pnpm exec oxfmt --write changelog.md

gen-diff:  ## (Release) generate the changelog diff between the current schema and the last version
	$(eval last_version := $(shell git tag --list 'version/*' --sort 'version:refname' | grep -vE 'rc[0-9]+$$' | tail -1))
	git show ${last_version}:schema.yml > schema-old.yml
	docker compose -f scripts/compose.yml run --rm --user "${UID}:${GID}" diff \
		--markdown \
		/local/diff.md \
		/local/schema-old.yml \
		/local/schema.yml
	rm schema-old.yml
	$(SED_INPLACE) 's/{/\&#123;/g' diff.md
	$(SED_INPLACE) 's/}/\&#125;/g' diff.md
	pnpm exec oxfmt --write diff.md

gen-client-go:  ## Build and install the authentik API for Golang
	$(UV) run make -C "${PWD}/packages/client-go" build

gen-client-rust:  ## Build and install the authentik API for Rust
	$(UV) run make -C "${PWD}/packages/client-rust" build version=${NPM_VERSION}
	make lint-fix-rust

gen-client-ts:  ## Build and install the authentik API for Typescript into the authentik UI Application
	make -C "${PWD}/packages/client-ts" build
	pnpm --dir web install

_gen-clients: gen-client-go gen-client-rust gen-client-ts
gen-clients:  ## Build and install API clients used by authentik
	$(MAKE) _gen-clients -j

gen: gen-build gen-clients  ## Build and install API schema and clients used by authentik

gen-dev-config:  ## Generate a local development config file
	$(UV) run scripts/generate_config.py

#########################
## Node.js
#########################

# Lifecycle scripts are blocked by default in pnpm 10+ via
# `pnpm-workspace.yaml#onlyBuiltDependencies`. Adding a package to that list
# grants it arbitrary code execution at install — audit at review time.

node-preinstall:  ## Verify the active Node.js and pnpm versions match what's in package.json.
	node ./scripts/node/lint-runtime.ts

node-install: node-preinstall  ## Install the necessary libraries to build Node.js packages and build the shared lint configs
	pnpm install --frozen-lockfile
	pnpm run build:lint-config

#########################
## Web
#########################

web-install:  ## Install the necessary libraries to build the authentik front end
	pnpm --dir web install --frozen-lockfile

web-build: node-install  ## Build the authentik front end
	pnpm --dir web run build

web: web-lint-fix web-lint web-check-compile  ## Format and lint the front-end, run lit-analyzer and type-check

web-check: ## Run front-end lint and format checks (does no modifications)
	pnpm --dir web lint:check
	pnpm --dir web format:check

web-test-unit:  ## Run web front-end tests once
	pnpm --dir web run test:unit

web-test:  ## Run tests for the authentik front end in watch mode
	pnpm --dir web run test

web-test-e2e:  ## Run front end Playwright end-to-end tests
	pnpm --dir web run test:e2e

web-test-visual:  ## Run visual regression tests for the front-end
	pnpm --dir web run test:visual

web-watch:  ## Build and watch the authentik front end for changes, updating automatically
	pnpm --dir web run watch

web-storybook-watch:  ## Build and run the storybook documentation server
	pnpm --dir web run storybook

web-lint-fix:  ## Format the front end source (oxfmt)
	pnpm --dir web run format

web-lint:  ## Lint the front end (oxfmt) and run lit-analyzer
	pnpm --dir web run lint
	pnpm --dir web run lit-analyse

web-check-compile:  ## Type-check the front end
	pnpm --dir web run tsc

web-i18n-extract:
	pnpm --dir web run extract-locales

#########################
## Docs
#########################

docs: docs-lint-fix docs-build  ## Spellcheck, format, and build the docs website

docs-install: node-install  ## Install the necessary libraries to build the authentik documentation
	pnpm --dir website install --frozen-lockfile

docs-lint-fix: lint-spellcheck  ## Spellcheck and format the documentation site
	pnpm --dir website run lint
	pnpm --dir website run format

docs-build:  ## Build the docs website
	node ./scripts/node/lint-runtime.ts website
	pnpm --dir website run build

docs-watch:  ## Build and watch the topics documentation
	pnpm --dir website run start

docs-test:  ## Run the documentation website tests
	pnpm --dir website run test

docs-check:  ## Run documentation lint, typecheck, and format (does no modifications)
	pnpm --dir website run lint:check
	pnpm --dir website run build:types
	pnpm --dir website run format:check

integrations: docs-lint-fix integrations-build  ## Spellcheck, format, and build the integrations website

integrations-build:  ## Build the integrations website
	pnpm --dir website run build:integrations

integrations-watch:  ## Build and watch the Integrations documentation
	pnpm --dir website/integrations run start

docs-api-build:  ## Build the API reference site
	pnpm --dir website run build:api

docs-api-watch:  ## Build and watch the API documentation
	pnpm --dir website/api run generate
	pnpm --dir website/api run start

docs-api-clean:  ## Clean generated API documentation
	pnpm --dir website/api run clean

#########################
## Docker
#########################

docker:  ## Build a docker image of the current source tree
	DOCKER_BUILDKIT=1 docker build . -f lifecycle/container/Dockerfile --progress plain --tag ${DOCKER_IMAGE}

test-docker:  ## Build docker image and run full test suite in the container compose stack
	BUILD=true ${PWD}/scripts/test_docker.sh

#########################
## CI
#########################
# These targets are use by GitHub actions to allow usage of matrix
# which makes the YAML File a lot smaller

ci--meta-debug:
	$(UV) run python -V || echo "No python installed"
	$(CARGO) --version || echo "No rust installed"
	node --version || echo "No node installed"

ci-lint-mypy: ci--meta-debug
	$(UV) run mypy --strict $(PY_SOURCES)

ci-lint-black: ci--meta-debug
	$(UV) run black --check $(PY_SOURCES)

ci-lint-ruff: ci--meta-debug
	$(UV) run ruff check $(PY_SOURCES)

ci-lint-spellcheck: ci--meta-debug
	npm run lint:spellcheck

ci-lint-bandit: ci--meta-debug
	$(UV) run bandit -c pyproject.toml -r $(PY_SOURCES) -iii

ci-lint-pending-migrations: ci--meta-debug
	$(UV) run python -m manage makemigrations --check

ci-lint-cargo-deny: ci--meta-debug
	$(CARGO) deny --config "${PWD}/.cargo/deny.toml" --locked --workspace check

ci-lint-cargo-machete: ci--meta-debug
	$(CARGO) machete

ci-lint-rustfmt: ci--meta-debug
	$(CARGO) +nightly fmt --all --check -- --config-path "${PWD}/.cargo/rustfmt.toml"

ci-lint-clippy: ci--meta-debug
	$(CARGO) clippy --workspace --all-targets -- -D warnings

ci-lint-catalogs: ci--meta-debug
	node ./scripts/node/lint-catalogs.ts

ci-lint-locales: ci--meta-debug
	$(UV) run python scripts/locales.py check

ci-lint-oxlint-fixtures: ci--meta-debug
	pnpm --filter @goauthentik/oxlint-config run build
	pnpm --filter @goauthentik/oxlint-config run verify

ci-lint-check-types: ci--meta-debug
	pnpm run build:types

ci-test: ci--meta-debug
	$(UV) run coverage run manage.py test --keepdb --parallel auto authentik
	$(UV) run coverage combine
	$(UV) run coverage report
	$(UV) run coverage xml

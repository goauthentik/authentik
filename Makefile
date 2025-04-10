.PHONY: gen dev-reset all clean test web website

.SHELLFLAGS += ${SHELLFLAGS} -e
PWD = $(shell pwd)
UID = $(shell id -u)
GID = $(shell id -g)
NPM_VERSION = $(shell python -m scripts.generate_semver)
PY_SOURCES = authentik tests scripts lifecycle .github
DOCKER_IMAGE ?= "authentik:test"

GEN_API_TS = "gen-ts-api"
GEN_API_PY = "gen-py-api"
GEN_API_GO = "gen-go-api"

pg_user := $(shell uv run python -m authentik.lib.config postgresql.user 2>/dev/null)
pg_host := $(shell uv run python -m authentik.lib.config postgresql.host 2>/dev/null)
pg_name := $(shell uv run python -m authentik.lib.config postgresql.name 2>/dev/null)

all: lint-fix lint test gen web  ## Lint, build, and test everything

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

node-check-compile: ## Check and compile the TypeScript source code
	npm run typecheck

node-lint-fix: ## Lint and automatically fix errors in the javascript source code
	lint-codespell
	npm run lint:fix

lint-fix: lint-codespell  ## Lint and automatically fix errors in the python source code. Reports spelling errors.
	uv run black $(PY_SOURCES)
	uv run ruff check --fix $(PY_SOURCES)

lint-codespell:  ## Reports spelling errors.
	uv run codespell -w

lint: ## Lint the python and golang sources
	uv run bandit -c pyproject.toml -r $(PY_SOURCES)
	golangci-lint run -v

migrate: ## Run the Authentik Django server's migrations
	uv run python -m lifecycle.migrate

i18n-extract: core-i18n-extract web-i18n-extract  ## Extract strings that require translation into files to send to a translation service

aws-cfn:
	cd lifecycle/aws && npm run aws-cfn

run:  ## Run the main authentik server process
	uv run ak server

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

install:  ## Install all requires dependencies for `web`, `website` and `core`
	npm ci
	uv sync --frozen

dev-drop-db:
	dropdb -U ${pg_user} -h ${pg_host} ${pg_name}
	# Also remove the test-db if it exists
	dropdb -U ${pg_user} -h ${pg_host} test_${pg_name} || true
	redis-cli -n 0 flushall

dev-create-db:
	createdb -U ${pg_user} -h ${pg_host} ${pg_name}

dev-reset: dev-drop-db dev-create-db migrate  ## Drop and restore the Authentik PostgreSQL instance to a "fresh install" state.

#########################
## API Schema
#########################

gen-build:  ## Extract the schema from the database
	AUTHENTIK_DEBUG=true \
		AUTHENTIK_TENANTS__ENABLED=true \
		AUTHENTIK_OUTPOSTS__DISABLE_EMBEDDED_OUTPOST=true \
		uv run ak make_blueprint_schema > blueprints/schema.json

	AUTHENTIK_DEBUG=true \
		AUTHENTIK_TENANTS__ENABLED=true \
		AUTHENTIK_OUTPOSTS__DISABLE_EMBEDDED_OUTPOST=true \
		uv run ak spectacular --file schema.yml

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

gen-clean-ts:  ## Remove generated API client for Typescript
	rm -rf ./${GEN_API_TS}/
	rm -rf ./web/node_modules/@goauthentik/api/

gen-clean-go:  ## Remove generated API client for Go
	rm -rf ./${GEN_API_GO}/

gen-clean-py:  ## Remove generated API client for Python
	rm -rf ./${GEN_API_PY}/

gen-clean: gen-clean-ts gen-clean-go gen-clean-py  ## Remove generated API clients

gen-client-ts: gen-clean-ts  ## Build and install the authentik API for Typescript into the authentik UI Application
	docker run \
		--rm -v ${PWD}:/local \
		--user ${UID}:${GID} \
		docker.io/openapitools/openapi-generator-cli:v7.11.0 generate \
		--input-spec /local/schema.yml \
		--generator-name typescript-fetch \
		--output /local/${GEN_API_TS} \
		--config /local/scripts/api-ts-config.yaml \
		--additional-properties=npmVersion=${NPM_VERSION} \
		--git-repo-id authentik \
		--git-user-id goauthentik

	npm install

gen-client-py: gen-clean-py ## Build and install the authentik API for Python

	docker run \
		--rm -v ${PWD}:/local \
		--user ${UID}:${GID} \
		docker.io/openapitools/openapi-generator-cli:v7.11.0 generate \
		--input-spec /local/schema.yml \
		--generator-name python \
		--output /local/${GEN_API_PY} \
		--config /local/scripts/api-py-config.yaml \
		--additional-properties=packageVersion=${NPM_VERSION} \
		--git-repo-id authentik \
		--git-user-id goauthentik

	pip install ./${GEN_API_PY}

gen-client-go: gen-clean-go  ## Build and install the authentik API for Golang
	mkdir -p ./${GEN_API_GO} ./${GEN_API_GO}/templates

	wget https://raw.githubusercontent.com/goauthentik/client-go/main/config.yaml \
		-O ./${GEN_API_GO}/config.yaml

	wget https://raw.githubusercontent.com/goauthentik/client-go/main/templates/README.mustache \
		-O ./${GEN_API_GO}/templates/README.mustache

	wget https://raw.githubusercontent.com/goauthentik/client-go/main/templates/go.mod.mustache \
		-O ./${GEN_API_GO}/templates/go.mod.mustache

	cp schema.yml ./${GEN_API_GO}/

	docker run \
		--rm -v ${PWD}/${GEN_API_GO}:/local \
		--user ${UID}:${GID} \
		docker.io/openapitools/openapi-generator-cli:v6.5.0 generate \
		--input-spec /local/schema.yml \
		--generator-name go \
		--output /local/ \
		--config /local/config.yaml

	go mod edit -replace goauthentik.io/api/v3=./${GEN_API_GO}

	rm -rf ./${GEN_API_GO}/config.yaml ./${GEN_API_GO}/templates/

gen-dev-config:  ## Generate a local development config file
	uv run scripts/generate_config.py

gen: gen-build gen-client-ts

#########################
## Web
#########################

web: web-lint-fix web-lint node-check-compile  ## Automatically fix formatting issues in the Authentik UI source code, lint the code, and compile it

web-test: ## Run tests for the Authentik UI
	npm run test -w @goauthentik/web

web-watch:  ## Build and watch the Authentik UI for changes, updating automatically
	npm run watch -w @goauthentik/web

web-storybook-watch:  ## Build and run the storybook documentation server
	npm run storybook -w @goauthentik/web

web-lint-fix:
	npm run prettier -w @goauthentik/web

web-lint:
	npm run lint -w @goauthentik/web
	npm run lit-analyse -w @goauthentik/web

web-i18n-extract:
	npm run extract-locales -w @goauthentik/web

#########################
## Website
#########################

website: node-lint-fix website-build  ## Automatically fix formatting issues in the Authentik website/docs source code, lint the code, and compile it

website-build:
	npm run build -w @goauthentik/docs

website-watch:  ## Build and watch the documentation website, updating automatically
	npm run watch -w @goauthentik/docs

#########################
## Docker
#########################

docker:  ## Build a docker image of the current source tree
	mkdir -p ${GEN_API_TS}
	DOCKER_BUILDKIT=1 docker build . --progress plain --tag ${DOCKER_IMAGE}

test-docker:
	BUILD=true ./scripts/test_docker.sh

#########################
## CI
#########################
# These targets are use by GitHub actions to allow usage of matrix
# which makes the YAML File a lot smaller

ci--meta-debug:
	python -V
	node --version

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

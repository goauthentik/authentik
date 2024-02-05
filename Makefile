.PHONY: gen dev-reset all clean test web-$@ website-$@

all: lint-fix lint test gen web-all website-all  ## Lint, build, and test everything

include scripts/common.mk

CODESPELL_ARGS = -D - -D .github/codespell-dictionary.txt \
		-I .github/codespell-words.txt \
		-S 'web/src/locales/**' \
		authentik \
		internal \
		cmd \
		web/src \
		website/src \
		website/blog \
		website/developer-docs \
		website/docs \
		website/integrations \
		website/src

test-go:
	go test -timeout 0 -v -race -cover ./...

test: ## Run the server tests and produce a coverage report (locally)
	coverage run manage.py test --keepdb authentik
	coverage html
	coverage report

lint-fix:  ## Lint and automatically fix errors in the python source code. Reports spelling errors.
	isort $(PY_SOURCES)
	black $(PY_SOURCES)
	ruff --fix $(PY_SOURCES)
	codespell -w $(CODESPELL_ARGS)

lint: ## Lint the python and golang sources
	bandit -r $(PY_SOURCES) -x node_modules
	./web/node_modules/.bin/pyright $(PY_SOURCES)
	pylint $(PY_SOURCES)
	golangci-lint run -v

core-install:
	poetry install

migrate: ## Run the Authentik Django server's migrations
	python -m lifecycle.migrate

i18n-extract: core-i18n-extract web-i18n-extract  ## Extract strings that require translation into files to send to a translation service

core-i18n-extract:
	ak makemessages --ignore web --ignore internal --ignore web --ignore web-api --ignore website -l en

install: web-install website-install core-install  ## Install all requires dependencies for `web`, `website` and `core`

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
		ak make_blueprint_schema > blueprints/schema.json
	AUTHENTIK_DEBUG=true \
		AUTHENTIK_TENANTS__ENABLED=true \
		AUTHENTIK_OUTPOSTS__DISABLE_EMBEDDED_OUTPOST=true \
		ak spectacular --file schema.yml

gen-changelog:  ## (Release) generate the changelog based from the commits since the last tag
	git log --pretty=format:" - %s" $(shell git describe --tags $(shell git rev-list --tags --max-count=1))...$(shell git branch --show-current) | sort > changelog.md
	npx prettier --write changelog.md

gen-diff:  ## (Release) generate the changelog diff between the current schema and the last tag
	git show $(shell git describe --tags $(shell git rev-list --tags --max-count=1)):schema.yml > old_schema.yml
	docker run \
		--rm -v ${PWD}:/local \
		--user ${UID}:${GID} \
		docker.io/openapitools/openapi-diff:2.1.0-beta.6 \
		--markdown /local/diff.md \
		/local/old_schema.yml /local/schema.yml
	rm old_schema.yml
	sed -i 's/{/&#123;/g' diff.md
	sed -i 's/}/&#125;/g' diff.md
	npx prettier --write diff.md

gen-clean-go:  ## Remove generated API client for Go
	rm -rf gen-go-api/

gen-clean: gen-clean-ts gen-clean-go  ## Remove generated API clients

gen-client-go: gen-clean-go  ## Build and install the authentik API for Golang
	mkdir -p ./gen-go-api ./gen-go-api/templates
	wget https://raw.githubusercontent.com/goauthentik/client-go/main/config.yaml -O ./gen-go-api/config.yaml
	wget https://raw.githubusercontent.com/goauthentik/client-go/main/templates/README.mustache -O ./gen-go-api/templates/README.mustache
	wget https://raw.githubusercontent.com/goauthentik/client-go/main/templates/go.mod.mustache -O ./gen-go-api/templates/go.mod.mustache
	cp schema.yml ./gen-go-api/
	docker run \
		--rm -v ${PWD}/gen-go-api:/local \
		--user ${UID}:${GID} \
		docker.io/openapitools/openapi-generator-cli:v6.5.0 generate \
		-i /local/schema.yml \
		-g go \
		-o /local/ \
		-c /local/config.yaml
	go mod edit -replace goauthentik.io/api/v3=./gen-go-api
	rm -rf ./gen-go-api/config.yaml ./gen-go-api/templates/

gen-dev-config:  ## Generate a local development config file
	python -m scripts.generate_config

gen: gen-build gen-client-ts

#########################
## Docker
#########################

docker:  ## Build a docker image of the current source tree
	DOCKER_BUILDKIT=1 docker build . --progress plain --tag ${DOCKER_IMAGE}

test-docker:  ## Run all tests in a docker-compose
	echo "PG_PASS=$(openssl rand -base64 32)" >> .env
	echo "AUTHENTIK_SECRET_KEY=$(openssl rand -base64 32)" >> .env
	docker-compose pull -q
	docker-compose up --no-start
	docker-compose start postgresql redis
	docker-compose run -u root server test-all
	rm -f .env

web-%:
	$(MAKE) -f ${BUILDDIR}/web/Makefile $(subst web-,,$@)

website-%:
	$(MAKE) -f ${BUILDDIR}/website/Makefile $(subst website-,,$@)

ci-%:
	$(MAKE) -f ${BUILDDIR}/scripts/ci.mk $(subst ci-,,$@)

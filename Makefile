.SHELLFLAGS += -x -e
PWD = $(shell pwd)
UID = $(shell id -u)
GID = $(shell id -g)
NPM_VERSION = $(shell python -m scripts.npm_version)

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

all: lint-fix lint test gen web

test-go:
	go test -timeout 0 -v -race -cover ./...

test-docker:
	echo "PG_PASS=$(openssl rand -base64 32)" >> .env
	echo "AUTHENTIK_SECRET_KEY=$(openssl rand -base64 32)" >> .env
	docker-compose pull -q
	docker-compose up --no-start
	docker-compose start postgresql redis
	docker-compose run -u root server test
	rm -f .env

test:
	coverage run manage.py test --keepdb authentik
	coverage html
	coverage report

lint-fix:
	isort authentik tests scripts lifecycle
	black authentik tests scripts lifecycle
	codespell -w $(CODESPELL_ARGS)

lint:
	pylint authentik tests lifecycle
	bandit -r authentik tests lifecycle -x node_modules
	golangci-lint run -v

migrate:
	python -m lifecycle.migrate

run:
	go run -v ./cmd/server/

i18n-extract: i18n-extract-core web-extract

i18n-extract-core:
	ak makemessages --ignore web --ignore internal --ignore web --ignore web-api --ignore website -l en

#########################
## API Schema
#########################

gen-build:
	AUTHENTIK_DEBUG=true ak make_blueprint_schema > blueprints/schema.json
	AUTHENTIK_DEBUG=true ak spectacular --file schema.yml

gen-diff:
	git show $(shell git describe --abbrev=0):schema.yml > old_schema.yml
	docker run \
		--rm -v ${PWD}:/local \
		--user ${UID}:${GID} \
		docker.io/openapitools/openapi-diff:2.1.0-beta.3 \
		--markdown /local/diff.md \
		/local/old_schema.yml /local/schema.yml
	rm old_schema.yml

gen-clean:
	rm -rf web/api/src/
	rm -rf api/

gen-client-ts:
	docker run \
		--rm -v ${PWD}:/local \
		--user ${UID}:${GID} \
		docker.io/openapitools/openapi-generator-cli:v6.0.0 generate \
		-i /local/schema.yml \
		-g typescript-fetch \
		-o /local/gen-ts-api \
		-c /local/scripts/api-ts-config.yaml \
		--additional-properties=npmVersion=${NPM_VERSION} \
		--git-repo-id authentik \
		--git-user-id goauthentik
	mkdir -p web/node_modules/@goauthentik/api
	cd gen-ts-api && npm i
	\cp -rfv gen-ts-api/* web/node_modules/@goauthentik/api

gen-client-go:
	wget https://raw.githubusercontent.com/goauthentik/client-go/main/config.yaml -O config.yaml
	mkdir -p templates
	wget https://raw.githubusercontent.com/goauthentik/client-go/main/templates/README.mustache -O templates/README.mustache
	wget https://raw.githubusercontent.com/goauthentik/client-go/main/templates/go.mod.mustache -O templates/go.mod.mustache
	docker run \
		--rm -v ${PWD}:/local \
		--user ${UID}:${GID} \
		docker.io/openapitools/openapi-generator-cli:v6.0.0 generate \
		-i /local/schema.yml \
		-g go \
		-o /local/gen-go-api \
		-c /local/config.yaml
	go mod edit -replace goauthentik.io/api/v3=./gen-go-api
	rm -rf config.yaml ./templates/

gen-dev-config:
	python -m scripts.generate_config

gen: gen-build gen-clean gen-client-ts

#########################
## Web
#########################

web-build: web-install
	cd web && npm run build

web: web-lint-fix web-lint web-check-compile

web-install:
	cd web && npm ci

web-watch:
	rm -rf web/dist/
	mkdir web/dist/
	touch web/dist/.gitkeep
	cd web && npm run watch

web-lint-fix:
	cd web && npm run prettier

web-lint:
	cd web && npm run lint
	cd web && npm run lit-analyse

web-check-compile:
	cd web && npm run tsc

web-extract:
	cd web && npm run extract

#########################
## Website
#########################

website: website-lint-fix website-build

website-install:
	cd website && npm ci

website-lint-fix:
	cd website && npm run prettier

website-build:
	cd website && npm run build

website-watch:
	cd website && npm run watch

# These targets are use by GitHub actions to allow usage of matrix
# which makes the YAML File a lot smaller
PY_SOURCES=authentik tests lifecycle
ci--meta-debug:
	python -V
	node --version

ci-pylint: ci--meta-debug
	pylint $(PY_SOURCES)

ci-black: ci--meta-debug
	black --check $(PY_SOURCES)

ci-codespell: ci--meta-debug
	codespell $(CODESPELL_ARGS) -s

ci-isort: ci--meta-debug
	isort --check $(PY_SOURCES)

ci-bandit: ci--meta-debug
	bandit -r $(PY_SOURCES)

ci-pyright: ci--meta-debug
	./web/node_modules/.bin/pyright $(PY_SOURCES)

ci-pending-migrations: ci--meta-debug
	ak makemigrations --check

install: web-install website-install
	poetry install

dev-reset:
	dropdb -U postgres -h localhost authentik
	createdb -U postgres -h localhost authentik
	redis-cli -n 0 flushall
	make migrate

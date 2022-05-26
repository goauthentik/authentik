.SHELLFLAGS += -x -e
PWD = $(shell pwd)
UID = $(shell id -u)
GID = $(shell id -g)
NPM_VERSION = $(shell python -m scripts.npm_version)

all: lint-fix lint test gen web

test-integration:
	coverage run manage.py test tests/integration

test-e2e-provider:
	coverage run manage.py test tests/e2e/test_provider*

test-e2e-rest:
	coverage run manage.py test tests/e2e/test_flows* tests/e2e/test_source*

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
	coverage run manage.py test authentik
	coverage html
	coverage report

lint-fix:
	isort authentik tests lifecycle
	black authentik tests lifecycle
	codespell -I .github/codespell-words.txt -S 'web/src/locales/**' -w \
		authentik \
		internal \
		cmd \
		web/src \
		website/src \
		website/docs \
		website/developer-docs

lint:
	bandit -r authentik tests lifecycle -x node_modules
	pylint authentik tests lifecycle
	golangci-lint run -v

i18n-extract: i18n-extract-core web-extract

i18n-extract-core:
	./manage.py makemessages --ignore web --ignore internal --ignore web --ignore web-api --ignore website -l en

gen-build:
	./manage.py spectacular --file schema.yml

gen-clean:
	rm -rf web/api/src/
	rm -rf api/

gen-client-web:
	docker run \
		--rm -v ${PWD}:/local \
		--user ${UID}:${GID} \
		openapitools/openapi-generator-cli:v6.0.0 generate \
		-i /local/schema.yml \
		-g typescript-fetch \
		-o /local/gen-ts-api \
		--additional-properties=typescriptThreePlus=true,supportsES6=true,npmName=@goauthentik/api,npmVersion=${NPM_VERSION}
	mkdir -p web/node_modules/@goauthentik/api
	\cp -fv scripts/web_api_readme.md gen-ts-api/README.md
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
		openapitools/openapi-generator-cli:v6.0.0 generate \
		-i /local/schema.yml \
		-g go \
		-o /local/gen-go-api \
		-c /local/config.yaml
	go mod edit -replace goauthentik.io/api/v3=./gen-go-api
	rm -rf config.yaml ./templates/

gen: gen-build gen-clean gen-client-web

migrate:
	python -m lifecycle.migrate

run:
	go run -v cmd/server/main.go

#########################
## Web
#########################

web: web-lint-fix web-lint web-extract

web-install:
	cd web && npm ci

web-watch:
	cd web && npm run watch

web-lint-fix:
	cd web && npm run prettier

web-lint:
	cd web && npm run lint
	cd web && npm run lit-analyse

web-extract:
	cd web && npm run extract

#########################
## Website
#########################

website: website-lint-fix

website-install:
	cd website && npm ci

website-lint-fix:
	cd website && npm run prettier

website-watch:
	cd website && npm run watch

# These targets are use by GitHub actions to allow usage of matrix
# which makes the YAML File a lot smaller

ci--meta-debug:
	python -V
	node --version

ci-pylint: ci--meta-debug
	pylint authentik tests lifecycle

ci-black: ci--meta-debug
	black --check authentik tests lifecycle

ci-isort: ci--meta-debug
	isort --check authentik tests lifecycle

ci-bandit: ci--meta-debug
	bandit -r authentik tests lifecycle

ci-pyright: ci--meta-debug
	pyright e2e lifecycle

ci-pending-migrations: ci--meta-debug
	./manage.py makemigrations --check

install: web-install website-install
	poetry install

a: install
	tmux \
		new-session 'make run' \; \
		split-window 'make web-watch'

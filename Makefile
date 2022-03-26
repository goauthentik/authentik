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

gen-web:
	docker run \
		--rm -v ${PWD}:/local \
		--user ${UID}:${GID} \
		openapitools/openapi-generator-cli:v5.4.0 generate \
		-i /local/schema.yml \
		-g typescript-fetch \
		-o /local/web-api \
		--additional-properties=typescriptThreePlus=true,supportsES6=true,npmName=@goauthentik/api,npmVersion=${NPM_VERSION}
	mkdir -p web/node_modules/@goauthentik/api
	python -m scripts.web_api_esm
	\cp -fv scripts/web_api_readme.md web-api/README.md
	cd web-api && npm i
	\cp -rfv web-api/* web/node_modules/@goauthentik/api

gen-outpost:
	wget https://raw.githubusercontent.com/goauthentik/client-go/main/config.yaml -O config.yaml
	mkdir -p templates
	wget https://raw.githubusercontent.com/goauthentik/client-go/main/templates/README.mustache -O templates/README.mustache
	wget https://raw.githubusercontent.com/goauthentik/client-go/main/templates/go.mod.mustache -O templates/go.mod.mustache
	docker run \
		--rm -v ${PWD}:/local \
		--user ${UID}:${GID} \
		openapitools/openapi-generator-cli:v5.2.1 generate \
		-i /local/schema.yml \
		-g go \
		-o /local/api \
		-c /local/config.yaml
	go mod edit -replace goauthentik.io/api=./api
	rm -rf config.yaml ./templates/

gen: gen-build gen-clean gen-web

migrate:
	python -m lifecycle.migrate

run:
	go run -v cmd/server/main.go

web-watch:
	cd web && npm run watch

web: web-lint-fix web-lint web-extract

web-lint-fix:
	cd web && npm run prettier

web-lint:
	cd web && npm run lint
	cd web && npm run lit-analyse

web-extract:
	cd web && npm run extract

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

install:
	poetry install
	cd web && npm i
	cd website && npm i

a: install
	tmux \
		new-session 'make run' \; \
		split-window 'make web-watch'

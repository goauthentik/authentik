.SHELLFLAGS += -x -e
PWD = $(shell pwd)
UID = $(shell id -u)
GID = $(shell id -g)
NPM_VERSION = $(shell python -m scripts.npm_version)

all: lint-fix lint test gen

test-integration:
	coverage run manage.py test -v 3 tests/integration

test-e2e:
	coverage run manage.py test --failfast -v 3 tests/e2e

test:
	coverage run manage.py test -v 3 authentik
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

i18n-extract:
	./manage.py makemessages --ignore web --ignore internal --ignore web --ignore web-api --ignore website -l en
	cd web && npm run extract

gen-build:
	./manage.py spectacular --file schema.yml

gen-clean:
	rm -rf web/api/src/
	rm -rf api/

gen-web:
	docker run \
		--rm -v ${PWD}:/local \
		--user ${UID}:${GID} \
		ghcr.io/beryju/openapi-generator generate \
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
		openapitools/openapi-generator-cli generate \
		-i /local/schema.yml \
		-g go \
		-o /local/api \
		-c /local/config.yaml
	go mod edit -replace goauthentik.io/api=./api

gen: gen-build gen-clean gen-web

migrate:
	python -m lifecycle.migrate

run:
	go run -v cmd/server/main.go

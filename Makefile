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

lint:
	pyright authentik tests lifecycle
	bandit -r authentik tests lifecycle -x node_modules
	pylint authentik tests lifecycle

gen-build:
	./manage.py spectacular --file schema.yml

gen-clean:
	rm -rf web/api/src/
	rm -rf api/

gen-web:
	docker run \
		--rm -v ${PWD}:/local \
		--user ${UID}:${GID} \
		openapitools/openapi-generator-cli generate \
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
	docker run \
		--rm -v ${PWD}:/local \
		--user ${UID}:${GID} \
		openapitools/openapi-generator-cli generate \
		--git-host goauthentik.io \
		--git-repo-id outpost \
		--git-user-id api \
		-i /local/schema.yml \
		-g go \
		-o /local/api \
		--additional-properties=packageName=api,enumClassPrefix=true,useOneOfDiscriminatorLookup=true,disallowAdditionalPropertiesIfNotPresent=false
	rm -f api/go.mod api/go.sum

gen: gen-build gen-clean gen-web gen-outpost

migrate:
	python -m lifecycle.migrate

run:
	go run -v cmd/server/main.go

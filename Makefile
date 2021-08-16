.SHELLFLAGS += -x -e
PWD = $(shell pwd)
UID = $(shell id -u)
GID = $(shell id -g)

all: lint-fix lint test gen

test-integration:
	k3d cluster create || exit 0
	k3d kubeconfig write -o ~/.kube/config --overwrite
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
		-o /local/web/api \
		--additional-properties=typescriptThreePlus=true,supportsES6=true,npmName=authentik-api,npmVersion=1.0.0
	# npm i runs tsc as part of the installation process
	cd web/api && npm i

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
		--additional-properties=packageName=api,enumClassPrefix=true,useOneOfDiscriminatorLookup=true
	rm -f api/go.mod api/go.sum

gen: gen-build gen-clean gen-web gen-outpost

migrate:
	python -m lifecycle.migrate

run:
	go run -v cmd/server/main.go

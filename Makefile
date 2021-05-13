.SHELLFLAGS += -x -e
PWD = $(shell pwd)

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

gen:
	./manage.py generate_swagger -o swagger.yaml -f yaml
	docker run \
		--rm -v ${PWD}:/local \
		openapitools/openapi-generator-cli generate \
		-i /local/swagger.yaml \
		-g typescript-fetch \
		-o /local/web/api \
		--additional-properties=typescriptThreePlus=true,supportsES6=true,npmName=authentik-api,npmVersion=1.0.0
	cd web/api && npx tsc

run:
	go run -v cmd/server/main.go

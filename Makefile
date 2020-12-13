all: lint-fix lint coverage gen

test-full:
	coverage run manage.py test --failfast -v 3 .
	coverage html
	coverage report

test-integration:
	k3d cluster create || exit 0
	k3d kubeconfig write -o ~/.kube/config --overwrite
	coverage run manage.py test --failfast -v 3 tests/integration

test-e2e:
	coverage run manage.py test --failfast -v 3 tests/e2e

coverage:
	coverage run manage.py test --failfast -v 3 authentik
	coverage html
	coverage report

lint-fix:
	isort -rc authentik tests lifecycle
	black authentik tests lifecycle

lint:
	pyright authentik tests lifecycle
	bandit -r authentik tests lifecycle -x node_modules
	pylint authentik tests lifecycle
	prospector

gen: coverage
	./manage.py generate_swagger -o swagger.yaml -f yaml

local-stack:
	export AUTHENTIK_TAG=testing
	docker build -t beryju/authentik:testng .
	docker-compose up -d
	docker-compose run --rm server migrate

build-static:
	docker-compose -f scripts/ci.docker-compose.yml up -d
	docker build -t beryju/authentik-static -f static.Dockerfile --network=scripts_default .
	docker-compose -f scripts/ci.docker-compose.yml down -v

all: lint-fix lint coverage gen

test-integration:
	k3d cluster create || exit 0
	k3d kubeconfig write -o ~/.kube/config --overwrite
	coverage run manage.py test --failfast -v 3 tests/integration

test-e2e:
	coverage run manage.py test --failfast -v 3 tests/e2e

coverage:
	coverage run manage.py test --failfast -v 3 passbook
	coverage html
	coverage report

lint-fix:
	isort -rc .
	black passbook tests lifecycle

lint:
	pyright passbook tests lifecycle
	bandit -r passbook tests lifecycle -x node_modules
	pylint passbook tests lifecycle
	prospector

gen: coverage
	./manage.py generate_swagger -o swagger.yaml -f yaml

local-stack:
	export PASSBOOK_TAG=testing
	docker build -t beryju/passbook:testng .
	docker-compose up -d
	docker-compose run --rm server migrate

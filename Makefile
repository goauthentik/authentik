all: lint-fix lint coverage gen

coverage:
	coverage run --concurrency=multiprocessing manage.py test passbook --failfast
	coverage combine
	coverage html
	coverage report

lint-fix:
	isort -rc .
	black .

lint:
	pyright
	bandit -r .
	pylint passbook
	prospector

gen: coverage
	./manage.py generate_swagger -o swagger.yaml -f yaml

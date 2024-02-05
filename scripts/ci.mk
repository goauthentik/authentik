#########################
## CI
#########################
# These targets are use by GitHub actions to allow usage of matrix
# which makes the YAML File a lot smaller

_meta-debug:
	python -V
	node --version

pylint: _meta-debug
	pylint $(PY_SOURCES)

black: _meta-debug
	black --check $(PY_SOURCES)

ruff: _meta-debug
	ruff check $(PY_SOURCES)

codespell: _meta-debug
	codespell $(CODESPELL_ARGS) -s

isort: _meta-debug
	isort --check $(PY_SOURCES)

bandit: _meta-debug
	bandit -r $(PY_SOURCES)

pyright: _meta-debug
	${BUILDDIR}/web/node_modules/.bin/pyright $(PY_SOURCES)

pending-migrations: _meta-debug
	ak makemigrations --check

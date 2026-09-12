.SHELLFLAGS += -x -e
PWD = $(shell pwd)
UID = $(shell id -u)
GID = $(shell id -g)

build:
	rm -rf src
	docker compose run --rm -T --user "${UID}:${GID}" gen \
		generate \
		-i /schema.yml \
		-g typescript-fetch \
		-o local \
		-c /local/config.yaml \
		--additional-properties=npmVersion=0.0.0 \
		--git-repo-id authentik \
		--git-user-id goauthentik
	rm -rf "${PWD}/.openapi-generator"
	node scripts/prepare-generated.mjs
	# Twice: the first pass leaves imports that only become unused once others are removed.
	npx oxlint --fix --fix-suggestions . && npx oxlint --fix --fix-suggestions .
	# Also twice: oxfmt does not always settle in one pass.
	npx oxfmt --write . && npx oxfmt --write .

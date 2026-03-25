.SHELLFLAGS += -x -e
PWD = $(shell pwd)
UID = $(shell id -u)
GID = $(shell id -g)

build:
	rm -rf src
	docker compose run --rm --user "${UID}:${GID}" gen \
		generate \
		-i /schema.yml \
		-g typescript-fetch \
		-o local \
		-c /local/config.yaml \
		--additional-properties=npmVersion=0.0.0 \
		--git-repo-id authentik \
		--git-user-id goauthentik
	rm -rf \
		.npmignore \
		.openapi-generator \
		docs \
		README.md

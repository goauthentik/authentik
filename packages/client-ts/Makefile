.SHELLFLAGS += -x -e
PWD = $(shell pwd)
UID = $(shell id -u)
GID = $(shell id -g)

build:
ifndef version
	$(error Usage: make build version=20xx.xx.xx)
endif
	rm -rf src
	docker compose run --rm --user "${UID}:${GID}" gen \
		generate \
		-i /schema.yml \
		-g typescript-fetch \
		-o local \
		-c /local/config.yaml \
		--additional-properties=packageVersion=$(version) \
		--git-repo-id authentik \
		--git-user-id goauthentik
	rm -rf \
		.npmignore \
		.openapi-generator \
		docs \
		README.md

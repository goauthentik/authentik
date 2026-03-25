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
		-g rust \
		-o local \
		-c /local/config.yaml \
		--additional-properties=packageVersion=$(version)
	rm -rf \
		.gitignore \
		.openapi-generator \
		.travis.yml \
		docs \
		git_push.sh \
		README.md

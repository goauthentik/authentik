.SHELLFLAGS += -x -e
PWD = $(shell pwd)
UID = $(shell id -u)
GID = $(shell id -g)

build:
ifndef version
	$(error Usage: make build version=20xx.xx.xx)
endif
	rm -rf *.go
	docker compose run --rm --user "${UID}:${GID}" gen \
		generate \
		-i /schema.yml \
		-g go \
		-o local \
		-c /local/config.yaml
	rm -rf \
		.gitignore \
		.openapi-generator \
		.travis.yml \
		README.md \
		api \
		docs \
		git_push.sh \
		test
	go fmt .

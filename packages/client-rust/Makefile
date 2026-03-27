.SHELLFLAGS += -x -e
PWD = $(shell pwd)
UID = $(shell id -u)
GID = $(shell id -g)

UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
	SED_INPLACE = sed -i ''
else
	SED_INPLACE = sed -i
endif

build:
ifndef version
	$(error Usage: make build version=20xx.xx.xx)
endif
	rm -rf "${PWD}/src"
	docker compose run --rm --user "${UID}:${GID}" gen \
		generate \
		-i /schema.yml \
		-g rust \
		-o local \
		-c /local/config.yaml \
		--additional-properties=packageVersion=$(version)
	$(SED_INPLACE) 's/models::models::/models::/g' ${PWD}/src/apis/*
	rm -rf \
		"${PWD}/.gitignore" \
		"${PWD}/.openapi-generator" \
		"${PWD}/.travis.yml" \
		"${PWD}/docs" \
		"${PWD}/git_push.sh" \
		"${PWD}/README.md"

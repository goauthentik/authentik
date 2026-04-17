.SHELLFLAGS += -x -e
PWD = $(shell pwd)
UID = $(shell id -u)
GID = $(shell id -g)

UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
	SED_INPLACE = /usr/bin/sed -i ''
else
	SED_INPLACE = sed -i
endif

build:
ifndef version
	$(error Usage: make build version=20xx.xx.xx)
endif
	rm -rf "${PWD}/src"
	"${PWD}/../../scripts/api_filter_schema.py" "${PWD}/../../schema.yml" "${PWD}/schema.yml" "${PWD}/operation_ids"
	docker compose run --rm --user "${UID}:${GID}" gen \
		generate \
		-i /local/schema.yml \
		-g rust \
		-o local \
		-c /local/config.yaml \
		--additional-properties=packageVersion=$(version)
	$(SED_INPLACE) 's/models::models::/models::/g' ${PWD}/src/apis/*
	rm -rf "${PWD}/.openapi-generator" "${PWD}/api/openapi.yaml" "${PWD}/schema.yml"

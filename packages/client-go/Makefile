.SHELLFLAGS += -x -e
PWD = $(shell pwd)
UID = $(shell id -u)
GID = $(shell id -g)

build:
	rm -rf "${PWD}"/*.go
	"${PWD}/../../scripts/api_filter_schema.py" "${PWD}/../../schema.yml" "${PWD}/schema.yml" "${PWD}/operation_ids"
	docker compose run --rm --user "${UID}:${GID}" gen \
		generate \
		-i /local/schema.yml \
		-g go \
		-o local \
		-c /local/config.yaml
	rm -rf "${PWD}/.openapi-generator" "${PWD}/api/openapi.yaml" "${PWD}/schema.yml"
	go fmt .

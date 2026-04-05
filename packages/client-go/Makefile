.SHELLFLAGS += -x -e
PWD = $(shell pwd)
UID = $(shell id -u)
GID = $(shell id -g)

build:
	rm -rf "${PWD}"/*.go
	docker compose run --rm --user "${UID}:${GID}" gen \
		generate \
		-i /schema.yml \
		-g go \
		-o local \
		-c /local/config.yaml
	rm -rf "${PWD}/.openapi-generator"
	go fmt .

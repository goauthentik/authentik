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
	rm -rf \
		"${PWD}/.gitignore" \
		"${PWD}/.openapi-generator" \
		"${PWD}/.travis.yml" \
		"${PWD}/README.md" \
		"${PWD}/api" \
		"${PWD}/docs" \
		"${PWD}/git_push.sh" \
		"${PWD}/test" \
		"${PWD}/go.mod" \
		"${PWD}/go.sum"
	go fmt .

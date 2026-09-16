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
	# Deliberately not formatted. The client is generated and read by the compiler, not edited,
	# so a formatter here buys nothing and couples every regeneration to a tool version and a
	# collation setting — which is how `git diff --exit-code` in CI ends up red.
	# Unused imports are a different matter — the generator emits them, and the Prettier plugin
	# that used to strip them is gone, so oxlint does that job.
	node scripts/prepare-generated.mjs
	# Twice: the first pass leaves imports that only become unused once others are removed.
	npx oxlint --fix --fix-suggestions . && npx oxlint --fix --fix-suggestions .

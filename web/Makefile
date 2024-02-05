.PHONY: all

all: lint-fix lint check-compile i18n-extract  ## Automatically fix formatting issues in the Authentik UI source code, lint the code, and compile it

BUILDDIR = $(shell git rev-parse --show-toplevel)
include ${BUILDDIR}/scripts/common.mk

#########################
## API Client
#########################

gen-clean-ts:  ## Remove generated API client for Typescript
	rm -rf ${BUILDDIR}/gen-ts-api/
	rm -rf ${BUILDDIR}/web/node_modules/@goauthentik/api/

gen-client-ts: gen-clean-ts  ## Build and install the authentik API for Typescript into the authentik UI Application
	docker run \
		--rm -v ${BUILDDIR}:/local \
		--user ${UID}:${GID} \
		docker.io/openapitools/openapi-generator-cli:v6.5.0 generate \
		-i /local/schema.yml \
		-g typescript-fetch \
		-o /local/gen-ts-api \
		-c /local/scripts/api-ts-config.yaml \
		--additional-properties=npmVersion=${NPM_VERSION} \
		--git-repo-id authentik \
		--git-user-id goauthentik
	mkdir -p ${BUILDDIR}/web/node_modules/@goauthentik/api
	cd ${BUILDDIR}/gen-ts-api && npm i
	cp -rf ${BUILDDIR}/gen-ts-api/* ${BUILDDIR}/web/node_modules/@goauthentik/api

#########################
## Web
#########################

build: install  ## Build the Authentik UI
	cd ${BUILDDIR}/web && npm run build

install:  ## Install the necessary libraries to build the Authentik UI
	cd ${BUILDDIR}/web && npm ci

watch:  ## Build and watch the Authentik UI for changes, updating automatically
	rm -rf web/dist/
	mkdir web/dist/
	touch web/dist/.gitkeep
	cd ${BUILDDIR}/web && npm run watch

storybook-watch:  ## Build and run the storybook documentation server
	cd ${BUILDDIR}/web && npm run storybook

lint-fix:
	cd ${BUILDDIR}/web && npm run prettier

lint:
	cd ${BUILDDIR}/web && npm run lint
	cd ${BUILDDIR}/web && npm run lit-analyse

check-compile:
	cd ${BUILDDIR}/web && npm run tsc

i18n-extract:
	cd ${BUILDDIR}/web && npm run extract-locales

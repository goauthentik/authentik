.PHONY: all

BUILDDIR = $(shell git rev-parse --show-toplevel)
include ${BUILDDIR}/scripts/common.mk

#########################
## Website
#########################

all: lint-fix build  ## Automatically fix formatting issues in the Authentik website/docs source code, lint the code, and compile it

install:
	cd ${BUILDDIR}/website && npm ci

lint-fix:
	cd ${BUILDDIR}/website && npm run prettier

build:
	cd ${BUILDDIR}/website && npm run build

watch:  ## Build and watch the documentation website, updating automatically
	cd ${BUILDDIR}/website && npm run watch

.SHELLFLAGS += ${SHELLFLAGS} -e
UID = $(shell id -u)
GID = $(shell id -g)
NPM_VERSION = $(shell python -m scripts.npm_version)
PY_SOURCES = authentik tests scripts lifecycle
DOCKER_IMAGE ?= "authentik:test"
BUILDDIR = $(shell git rev-parse --show-toplevel)
MAKE = $(shell which make)

pg_user := $(shell python -m authentik.lib.config postgresql.user 2>/dev/null)
pg_host := $(shell python -m authentik.lib.config postgresql.host 2>/dev/null)
pg_name := $(shell python -m authentik.lib.config postgresql.name 2>/dev/null)


HELP_WIDTH := $(shell grep -h '^[a-z][^ ]*:.*\#\#' $(MAKEFILE_LIST) 2>/dev/null | \
	cut -d':' -f1 | awk '{printf "%d\n", length}' | sort -rn | head -1)

help:  ## Show this help
	@echo "\nSpecify a command. The choices are:\n"
	@grep -Eh '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[0;36m%-$(HELP_WIDTH)s  \033[m %s\n", $$1, $$2}' | \
		sort
	@echo ""

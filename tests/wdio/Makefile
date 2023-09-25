.PHONY: help precommit admin-user test-good-login test-bad-login

help:  ## Show this help
	@echo "\nSpecify a command. The choices are:\n"
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	    awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[0;36m%-20s\033[m %s\n", $$1, $$2}'
	@echo ""

ROOT := $(shell git rev-parse --show-toplevel 2> /dev/null)
WDIO = npm run wdio
SPEC = $(WDIO) -- --logLevel warn --spec ./test/specs

LOCAL_BLUEPRINTS=$(ROOT)/blueprints/local

node_modules: ## Runs `npm install` to prepare this feature
	npm ci

precommit: node_modules  ## Run the precommit: spell check all comments, eslint with sonarJS, prettier-write
	npm run precommit

# Actual tests are down below:

$(ROOT)/blueprints/local/admin-user.yaml:
	mkdir -p $(LOCAL_BLUEPRINTS)
	cp ./blueprints/admin-user.yaml $(LOCAL_BLUEPRINTS)
	cd $(ROOT) && ak apply_blueprint local/admin-user.yaml


admin-user: $(ROOT)/blueprints/local/admin-user.yaml


test-good-login: node_modules admin-user  ## Test that we can log into the server. Requires a running instance of the server.
	$(SPEC)/good-login.ts


test-bad-login: node_modules admin-user  ## Test that bad usernames and passwords create appropriate error messages
	$(SPEC)/bad-logins.ts


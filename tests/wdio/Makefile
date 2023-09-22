.PHONY: help
help:  ## Show this help
	@echo "\nSpecify a command. The choices are:\n"
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	    awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[0;36m%-20s\033[m %s\n", $$1, $$2}'
	@echo ""

WDIO = npm run wdio
SPEC = $(WDIO) -- --spec ./test/specs

node_modules: ## Runs `npm install` to prepare this feature
	npm ci

.PHONY: precommit
precommit: node_modules  ## Run the precommit: spell check all comments, eslint with sonarJS, prettier-write
	npm run precommit

# Actual tests are down below:

.PHONY: test-good-login
test-good-login: node_modules  ## Test that we can log into the server. Requires a running instance of the server.
	$(SPEC)/good-login.ts

.PHONY: test-bad-login
test-bad-login: node_modules  ## Test that bad usernames and passwords create appropriate error messages
	$(SPEC)/bad-logins.ts

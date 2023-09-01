.PHONY: help
help:  ## Print out this help message.
	@M=$$(perl -ne 'm/((\w|-)*):.*##/ && print length($$1)."\n"' Makefile | \
		sort -nr | head -1) && \
		perl -ne "m/^((\w|-)*):.*##\s*(.*)/ && print(sprintf(\"%s: %s\t%s\n\", \$$1, \" \"x($$M-length(\$$1)), \$$3))" Makefile
	@echo ""
	@echo "Set env NODE_ENV to 'development' to run this against the dev server"
	@echo ""

.PHONY: update-local-chromedriver
update-local-chromedriver:  ## Update the chrome driver to match the local chrome version, restoring package.json
	@ scripts/update_local_chromedriver

.PHONY: check-chromedriver
check-chromedriver: ## Report if the chrome driver and the local chrome version match
	@ scripts/check_local_chromedriver

RUNNER=npx wdio wdio.conf.js 

.PHONY: application-plus-ldap
application-plus-ldap: check-chromedriver  ## Run the "Wizard: Application With LDAP Provider, successful" test
	@ ${RUNNER} --spec=./tests/application-plus-ldap.test.js



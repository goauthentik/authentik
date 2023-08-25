# '.PHONY' entries inform Make that there is no accompanying file in the
# repository that this command actually makes, and so Make should always run the
# command, rather than look for dependencies to see if it should be run.

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
check-chromedriver:
	@ scripts/check_local_chromedriver

RUNNER=npx wdio wdio.conf.js --spec ./tests/application_runner.js 

.PHONY: test-home-complex
test-home-complex: check-chromedriver  ## Run the "Complex Home Application" test
	${RUNNER} --application=./portfolios/home_full_home_application.json

.PHONY: test-home-carriage-hill
test-home-carriage-hill: check-chromedriver  ## Run the "Carriage Hill" test
	${RUNNER} --application=./portfolios/home_carriage-hill.json

.PHONY: test-home-mobile-home
test-home-mobile-home: check-chromedriver  ## Run the "Mobile Home" test
	${RUNNER} --application=./portfolios/home_mobile_home_application.json

.PHONY: test-home-florida-roofs
test-home-florida-roofs: check-chromedriver  ## Run the "Floride Roofs" test
	${RUNNER} --application=./portfolios/home_florida_roofs_gates_and_farms.json

.PHONY: test-home-townhome
test-home-townhome: check-chromedriver  ## Run the "Townhome / Policy Lapsed" test
	${RUNNER} --application=./portfolios/home_townhome_application.json

.PHONY: test-home-future-application
test-home-future-application: check-chromedriver  ## Run the "Future Purchase" test
	${RUNNER} --application=./portfolios/home_future_purchase_application.json

.PHONY: test-home-basic
test-home-basic: check-chromedriver  ## Run the "Basic Home Application" test
	${RUNNER} --application=./portfolios/home_application_with_error.json

.PHONY: test-home-and-auto
test-home-and-auto: check-chromedriver  ## Run the "Home & Auto" test
	${RUNNER} --application=./portfolios/ha_application.json

.PHONY: test-auto-full
test-auto-full: check-chromedriver  ## Run the "Auto, Two Drivers" test
	${RUNNER} --application=./portfolios/auto_two_driver_auto_application.json

.PHONY: test-auto-basic
test-auto-basic: check-chromedriver  ## Run the "Basic Auto" test
	${RUNNER} --application=./portfolios/auto_application.json

.PHONY: test-auto-two-cars
test-auto-two-cars: check-chromedriver  ## Run the "Two-Cars Auto" test
	${RUNNER} --application=./portfolios/auto_application_two_cars.json

.PHONY: test-auto-michigan
test-auto-michigan: check-chromedriver  ## Run the "Michigan Auto" test
	${RUNNER} --application=./portfolios/auto_michigan_auto_application.json

.PHONY: test-smoke
test-smoke: check-chromedriver  ## Run the "Complex Home, Home+Auto and Two-Cars Auto" tests, including unanswered flows
	${RUNNER} --application=./portfolios/ha_application.json \
		--application=./portfolios/home_full_home_application.json \
		--application=./portfolios/unanswered_ha_application.json \
		--application=./portfolios/auto_application_two_cars.json \
    --application=./portfolios/windmit/home_florida_windmit_empty.json \
    --application=./portfolios/windmit/home_florida_windmit_full.json

.PHONY: test-embedded
test-embedded: check-chromedriver  ## Run the "Complex Home, Home+Auto and Two-Cars Auto" tests, including unanswered flows in embedded mode
	BOWTIE_EMBEDDED=true ${RUNNER} --application=./portfolios/ha_application.json \
		--application=./portfolios/home_future_purchase_application.json \
		--application=./portfolios/home_full_home_application.json \
		--application=./portfolios/unanswered_ha_application.json \
		--application=./portfolios/auto_application_two_cars.json

.PHONY: test-all
test-all: check-chromedriver   ## Run all the tests! Warning: this currently takes about 20 minutes!
	${RUNNER}

.PHONY: scan-for-duplicate-ids
scan-for-duplicate-ids: check-chromedriver  ## Run 'Home Basic', cataloging duplicates.  Warning: SLOW
	npx wdio wdio.conf.js --spec ./tests/application_runner_with_dupe_scanner.js --application=./portfolios/home_application.json

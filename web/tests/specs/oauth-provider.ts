import ProviderWizardView from "#tests/pageobjects/provider-wizard.page";
import ProvidersListPage from "#tests/pageobjects/providers-list.page";
import SessionPage from "#tests/pageobjects/session.page";
import { ConsoleTestRunner } from "#tests/utils/logger";
import { findElementByDataset } from "#tests/utils/selectors";
import { $, expect } from "@wdio/globals";

describe("Configure OAuth2 Providers", () => {
    it("Should configure a simple OAuth2 Application", async () => {
        await SessionPage.login({
            to: ProvidersListPage.pathname,
        });

        await expect(ProvidersListPage.$pageHeader).resolves.toHaveText("Providers");

        ConsoleTestRunner.info("Looking new provider wizard...");
        await ProvidersListPage.$newProviderButton.waitForDisplayed({
            timeout: 2_000,
        });
        ConsoleTestRunner.info("Clicking new provider wizard...");
        await ProvidersListPage.$newProviderButton.click();

        ConsoleTestRunner.info("Waiting for wizard title...");
        await ProviderWizardView.$wizardTitle.waitForDisplayed({
            timeout: 5_000,
        });

        ConsoleTestRunner.info("Wizard title matches...");

        await expect(ProviderWizardView.$wizardTitle).resolves.toHaveText("New provider");

        ConsoleTestRunner.info("Looking for ak-wizard-page-type-create...");

        await $("ak-wizard-page-type-create").waitForDisplayed();

        const $ouidComponent = findElementByDataset("ouid-component-name", "oauth2provider");
        ConsoleTestRunner.info("Scrolling to component...");
        $ouidComponent.scrollIntoView();

        ConsoleTestRunner.info("Clicking component...");
        await $ouidComponent.click();

        ConsoleTestRunner.info("Waiting for next button to be enabled...");
        await ProviderWizardView.$nextButton.waitForEnabled();

        ConsoleTestRunner.info("Clicking next...");
        await ProviderWizardView.$nextButton.click();

        ConsoleTestRunner.info("Waiting for form page to load...");

        await ProviderWizardView.$OAuth2ProviderForm.waitForExist({
            timeout: 5000,
        });

        ConsoleTestRunner.info("Waiting for form page to be displayed...");
        await ProviderWizardView.$OAuth2ProviderForm.waitForDisplayed({
            timeout: 5000,
        });

        ConsoleTestRunner.info("Done!");
    });
});

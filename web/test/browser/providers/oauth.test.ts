import { expect, test } from "#e2e";
import { ProvidersListFixture } from "#e2e/fixtures/providers-list";
import { ConsoleLogger } from "#logger/node";
import ProviderWizardView from "#tests/pageobjects/provider-wizard.page";
import { findElementByDataset } from "#tests/utils/selectors";

test.describe("Configure OAuth2 Providers", () => {
    test("Should configure a simple OAuth2 Application", async ({
        session,
        providersList,
        landmarks,
    }) => {
        await session.login({
            to: ProvidersListFixture.pathname,
        });

        await expect(landmarks.$pageHeading).toHaveText("Providers");

        ConsoleLogger.info("Looking new provider wizard...");
        await providersList.$newProviderButton.waitForDisplayed({
            timeout: 2_000,
        });

        ConsoleLogger.info("Clicking new provider wizard...");
        await providersList.$newProviderButton.click();

        ConsoleLogger.info("Waiting for wizard title...");
        await ProviderWizardView.$wizardTitle.waitForDisplayed({
            timeout: 5_000,
        });

        ConsoleLogger.info("Wizard title matches...");

        await expect(ProviderWizardView.$wizardTitle).resolves.toHaveText("New provider");

        await $("ak-wizard-page-type-create").waitForDisplayed();

        const $ouidComponent = findElementByDataset("ouid-component-name", "oauth2provider");
        ConsoleLogger.info("Scrolling to component...");
        $ouidComponent.scrollIntoView();

        await $ouidComponent.click();

        await ProviderWizardView.$nextButton.waitForEnabled();

        await ProviderWizardView.$nextButton.click();

        await ProviderWizardView.$OAuth2ProviderForm.waitForExist({
            timeout: 5000,
        });

        await ProviderWizardView.$OAuth2ProviderForm.waitForDisplayed({
            timeout: 5000,
        });

        ConsoleLogger.info("Done!");
    });
});

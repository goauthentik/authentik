import { expect } from "@wdio/globals";

import ProviderWizardView from "../pageobjects/provider-wizard.page.js";
import ProvidersListPage from "../pageobjects/providers-list.page.js";
import { randomId } from "../utils/index.js";
import { login } from "../utils/login.js";

async function reachTheProvider() {
    await ProvidersListPage.logout();
    await login();
    await ProvidersListPage.open();
    await expect(await ProvidersListPage.pageHeader).toHaveText("Providers");

    await ProvidersListPage.startWizardButton.click();
    await ProviderWizardView.wizardTitle.waitForDisplayed();
    await expect(await ProviderWizardView.wizardTitle).toHaveText("New provider");
}

describe("Configure Oauth2 Providers", () => {
    it("Should configure a simple LDAP Application", async () => {
        const newProviderName = `New OAuth2 Provider - ${randomId()}`;

        await reachTheProvider();

        await ProviderWizardView.providerList.waitForDisplayed();
        // @ts-expect-error "TSC does not understand metaprogramming."
        await ProviderWizardView.oauth2Provider.scrollIntoView();
        // @ts-expect-error "TSC does not understand metaprogramming."
        await ProviderWizardView.oauth2Provider.click();
        await ProviderWizardView.nextButton.click();
        await ProviderWizardView.pause();

        // @ts-expect-error "TSC does not understand ChainablePromiseElement"
        await ProviderWizardView.oauth.providerName.setValue(newProviderName);
        await ProviderWizardView.oauth.setAuthorizationFlow(
            "default-provider-authorization-explicit-consent",
        );
        await ProviderWizardView.nextButton.click();
        await ProviderWizardView.pause();

        await ProvidersListPage.searchInput.setValue(newProviderName);
        await ProvidersListPage.clickSearchButton();
        await ProvidersListPage.pause();

        const newProvider = await ProvidersListPage.findProviderRow();
        await newProvider.waitForDisplayed();
        expect(newProvider).toExist();
        expect(await newProvider.getText()).toHaveText(newProviderName);
    });
});

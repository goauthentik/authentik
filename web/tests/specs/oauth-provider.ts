import { expect } from "@wdio/globals";
import {
    clickButton,
    setFormGroup,
    setSearchSelect,
    setTextInput,
    setTypeCreate,
} from "pageobjects/controls.js";

import ProviderWizardView from "../pageobjects/provider-wizard.page.js";
import ProvidersListPage from "../pageobjects/providers-list.page.js";
import { randomId } from "../utils/index.js";
import { login } from "../utils/login.js";

async function reachTheProvider() {
    await ProvidersListPage.logout();
    await login();
    await ProvidersListPage.open();
    await expect(await ProvidersListPage.pageHeader()).toHaveText("Providers");

    await ProvidersListPage.startWizardButton.click();
    await ProviderWizardView.wizardTitle.waitForDisplayed();
    await expect(await ProviderWizardView.wizardTitle).toHaveText("New provider");
}

async function fillOutFields(fields: FieldDesc[]) {
    for (const field of fields) {
        const thefunc = field[0];
        const args = field.slice(1);
        await thefunc.apply($, args);
    }
}

describe("Configure Oauth2 Providers", () => {
    it("Should configure a simple LDAP Application", async () => {
        const newProviderName = `New OAuth2 Provider - ${randomId()}`;

        await reachTheProvider();

        await $("ak-wizard-page-type-create").waitForDisplayed();
        await setTypeCreate("selectProviderType", "OAuth2/OpenID Provider");
        await clickButton("Next");

        // prettier-ignore
        await fillOutFields([
            [setTextInput, "name", newProviderName],
            [setFormGroup, "Flow settings", "open"],
            [setSearchSelect, "authenticationFlow", "default-authentication-flow"],
            [setSearchSelect, "authorizationFlow", "default-provider-authorization-explicit-consent"],
            [setSearchSelect, "invalidationFlow", "default-invalidation-flow"],
        ]);

        await ProviderWizardView.pause();
        await ProviderWizardView.nextButton.click();
    });
});

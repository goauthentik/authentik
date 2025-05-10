/// <reference types="@wdio/globals/types" />
import { waitFor } from "tests/utils/timers";

import ProviderWizardView from "../pageobjects/provider-wizard.page.js";
import ProvidersListPage from "../pageobjects/providers-list.page.js";
import SessionPage from "../pageobjects/session.page.js";

async function reachTheProvider() {
    await SessionPage.logout();
    await SessionPage.login();
    await ProvidersListPage.navigate();
    await expect(ProvidersListPage.$pageHeader).resolves.toHaveText("Providers");

    await ProvidersListPage.$startWizardButton.click();
    await ProviderWizardView.$wizardTitle.waitForDisplayed();
    await expect(ProviderWizardView.$wizardTitle).resolves.toHaveText("New provider");
}

describe("Configure Oauth2 Providers", () => {
    it("Should configure a simple LDAP Application", async () => {
        await reachTheProvider();

        await $(">>>ak-wizard-page-type-create").waitForDisplayed();
        await $('>>>div[data-ouid-component-name="oauth2provider"]').scrollIntoView();
        await $('>>>div[data-ouid-component-name="oauth2provider"]').click();

        await ProviderWizardView.$nextButton.click();
        await waitFor();

        return $('>>>ak-form-element-horizontal[name="name"]').$(">>>input");
    });
});

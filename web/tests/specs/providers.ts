import { expect } from "@wdio/globals";

import ProviderWizardView from "../pageobjects/provider-wizard.page.js";
import ProvidersListPage from "../pageobjects/providers-list.page.js";
import { login } from "../utils/login.js";
import {
    simpleLDAPProviderForm,
    simpleOAuth2ProviderForm,
    simpleRadiusProviderForm,
} from "./shared-sequences.js";

async function reachTheProvider() {
    await ProvidersListPage.logout();
    await login();
    await ProvidersListPage.open();
    await expect(await ProvidersListPage.pageHeader()).toHaveText("Providers");
    await expect(await containedMessages()).not.toContain("Successfully created provider.");

    await ProvidersListPage.startWizardButton.click();
    await ProviderWizardView.wizardTitle.waitForDisplayed();
    await expect(await ProviderWizardView.wizardTitle).toHaveText("New provider");
}

const containedMessages = async () =>
    await (async () => {
        const messages = [];
        for await (const alert of $("ak-message-container").$$("ak-message")) {
            messages.push(await alert.$("p.pf-c-alert__title").getText());
        }
        return messages;
    })();

const hasProviderSuccessMessage = async () =>
    await browser.waitUntil(
        async () => (await containedMessages()).includes("Successfully created provider."),
        { timeout: 1000, timeoutMsg: "Expected to see provider success message." },
    );

type FieldDesc = [(..._: unknown) => Promise<void>, ...unknown];

async function fillOutFields(fields: FieldDesc[]) {
    for (const field of fields) {
        const thefunc = field[0];
        const args = field.slice(1);
        await thefunc.apply($, args);
    }
}

describe("Configure Oauth2 Providers", () => {
    it("Should configure a simple OAuth2 Provider", async () => {
        await reachTheProvider();
        await $("ak-wizard-page-type-create").waitForDisplayed();
        await fillOutFields(simpleOAuth2ProviderForm());
        await ProviderWizardView.pause();
        await ProviderWizardView.nextButton.click();
        await hasProviderSuccessMessage();
    });
});

describe("Configure LDAP Providers", () => {
    it("Should configure a simple LDAP Provider", async () => {
        await reachTheProvider();
        await $("ak-wizard-page-type-create").waitForDisplayed();
        await fillOutFields(simpleLDAPProviderForm());
        await ProviderWizardView.pause();
        await ProviderWizardView.nextButton.click();
        await hasProviderSuccessMessage();
    });
});

describe("Configure Radius Providers", () => {
    it("Should configure a simple Radius Provider", async () => {
        await reachTheProvider();
        await $("ak-wizard-page-type-create").waitForDisplayed();
        await fillOutFields(simpleRadiusProviderForm());
        await ProviderWizardView.pause();
        await ProviderWizardView.nextButton.click();
        await hasProviderSuccessMessage();
    });
});

describe("Configure SAML Providers", () => {
    it("Should configure a simple Radius Provider", async () => {
        await reachTheProvider();
        await $("ak-wizard-page-type-create").waitForDisplayed();
        await fillOutFields(simpleRadiusProviderForm());
        await ProviderWizardView.pause();
        await ProviderWizardView.nextButton.click();
        await hasProviderSuccessMessage();
    });
});

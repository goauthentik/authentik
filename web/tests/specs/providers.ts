import { expect } from "@wdio/globals";

import ProviderWizardView from "../pageobjects/provider-wizard.page.js";
import ProvidersListPage from "../pageobjects/providers-list.page.js";
import { login } from "../utils/login.js";
import { type TestSequence } from "./shared-sequences";
import {
    simpleForwardAuthDomainProxyProviderForm,
    simpleForwardAuthProxyProviderForm,
    simpleLDAPProviderForm,
    simpleOAuth2ProviderForm,
    simpleProxyProviderForm,
    simpleRadiusProviderForm,
    simpleSAMLProviderForm,
    simpleSCIMProviderForm,
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

async function fillOutFields(fields: TestSequence) {
    for (const field of fields) {
        const thefunc = field[0];
        const args = field.slice(1);
        // @ts-expect-error "This is a pretty alien call; I'm not surprised Typescript hates it."
        await thefunc.apply($, args);
    }
}

async function itShouldConfigureASimpleProvider(name: string, provider: TestSequence) {
    it(`Should successfully configure a ${name} provider`, async () => {
        await reachTheProvider();
        await $("ak-wizard-page-type-create").waitForDisplayed();
        await fillOutFields(provider);
        await ProviderWizardView.pause();
        await ProviderWizardView.nextButton.click();
        await hasProviderSuccessMessage();
    });
}

describe("Configuring Providers", () => {
    const providers = [
        ["LDAP", simpleLDAPProviderForm],
        ["OAuth2", simpleOAuth2ProviderForm],
        ["Radius", simpleRadiusProviderForm],
        ["SAML", simpleSAMLProviderForm],
        ["SCIM", simpleSCIMProviderForm],
        ["Proxy", simpleProxyProviderForm],
        ["Forward Auth (single application)", simpleForwardAuthProxyProviderForm],
        ["Forward Auth (domain level)", simpleForwardAuthDomainProxyProviderForm],
    ];

    for (const [name, provider] of providers) {
        itShouldConfigureASimpleProvider(name, provider());
    }
});

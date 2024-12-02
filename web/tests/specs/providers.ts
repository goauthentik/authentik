import { expect } from "@wdio/globals";

import { type TestProvider, type TestSequence } from "../pageobjects/controls";
import ProviderWizardView from "../pageobjects/provider-wizard.page.js";
import ProvidersListPage from "../pageobjects/providers-list.page.js";
import { login } from "../utils/login.js";
import {
    completeForwardAuthDomainProxyProviderForm,
    completeForwardAuthProxyProviderForm,
    completeLDAPProviderForm,
    completeOAuth2ProviderForm,
    completeProxyProviderForm,
    completeRadiusProviderForm,
    completeSAMLProviderForm,
    completeSCIMProviderForm,
    simpleForwardAuthDomainProxyProviderForm,
    simpleForwardAuthProxyProviderForm,
    simpleLDAPProviderForm,
    simpleOAuth2ProviderForm,
    simpleProxyProviderForm,
    simpleRadiusProviderForm,
    simpleSAMLProviderForm,
    simpleSCIMProviderForm,
} from "./provider-shared-sequences.js";

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
        // @ts-expect-error "This is a pretty alien call, so I'm not surprised Typescript doesn't like it."
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

type ProviderTest = [string, TestProvider];

describe("Configuring Providers", () => {
    const providers: ProviderTest[] = [
        ["Simple LDAP", simpleLDAPProviderForm],
        ["Simple OAuth2", simpleOAuth2ProviderForm],
        ["Simple Radius", simpleRadiusProviderForm],
        ["Simple SAML", simpleSAMLProviderForm],
        ["Simple SCIM", simpleSCIMProviderForm],
        ["Simple Proxy", simpleProxyProviderForm],
        ["Simple Forward Auth (single application)", simpleForwardAuthProxyProviderForm],
        ["Simple Forward Auth (domain level)", simpleForwardAuthDomainProxyProviderForm],
        ["Complete OAuth2", completeOAuth2ProviderForm],
        ["Complete LDAP", completeLDAPProviderForm],
        ["Complete Radius", completeRadiusProviderForm],
        ["Complete SAML", completeSAMLProviderForm],
        ["Complete SCIM", completeSCIMProviderForm],
        ["Complete Proxy", completeProxyProviderForm],
        ["Complete Forward Auth (single application)", completeForwardAuthProxyProviderForm],
        ["Complete Forward Auth (domain level)", completeForwardAuthDomainProxyProviderForm],
    ];

    for (const [name, provider] of providers) {
        itShouldConfigureASimpleProvider(name, provider());
    }
});

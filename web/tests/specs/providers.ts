import { expect } from "@wdio/globals";

import { type TestAction, type TestSequence, runTestSequence } from "../pageobjects/controls";
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

/**
 * Get all the messages in the message container.
 */
async function containedMessages(): Promise<string[]> {
    return await (async () => {
        const messages = [];
        for await (const alert of $("ak-message-container").$$("ak-message")) {
            messages.push(await alert.$("p.pf-c-alert__title").getText());
        }
        return messages;
    })();
}

async function reachTheProvider() {
    await ProvidersListPage.logout();
    await login();
    await ProvidersListPage.open();
    await expect(ProvidersListPage.pageHeader()).toHaveText("Providers");
    await expect(await containedMessages()).not.toContain("Successfully created provider.");

    await ProvidersListPage.startWizardButton.click();
    await ProviderWizardView.wizardTitle.waitForDisplayed();
    await expect(ProviderWizardView.wizardTitle).toHaveText("New provider");
}

/**
 * Wait for the provider success message to appear.
 */
async function providerSuccessMessagePresent(): Promise<true> {
    return browser.waitUntil(
        async () => {
            const messages = await containedMessages();
            return messages.includes("Successfully created provider.");
        },
        { timeout: 1000, timeoutMsg: "Expected to see provider success message." },
    );
}

async function itShouldConfigureASimpleProvider(name: string, provider: TestAction[]) {
    it(`Should successfully configure a ${name} provider`, async () => {
        await reachTheProvider();
        await $("ak-wizard-page-type-create").waitForDisplayed();

        await runTestSequence(provider);

        await ProviderWizardView.pause();
        await ProviderWizardView.nextButton.click();
        await providerSuccessMessagePresent();
    });
}

type ProviderTest = [string, TestSequence];

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

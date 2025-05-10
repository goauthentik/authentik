/// <reference types="@wdio/globals/types" />
import { waitFor } from "tests/utils/timers";

import ProviderWizardView from "../pageobjects/provider-wizard.page.js";
import ProvidersListPage from "../pageobjects/providers-list.page.js";
import SessionPage from "../pageobjects/session.page.js";
import { type TestAction, type TestSequence, runTestSequence } from "../utils/controls";
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
    return $("ak-message-container")
        .$$("ak-message")
        .map((alert) => {
            return alert.$("p.pf-c-alert__title").getText();
        });
}

async function reachTheProvider() {
    await SessionPage.logout();
    await SessionPage.login();

    await ProvidersListPage.navigate();

    await expect(ProvidersListPage.$pageHeader).resolves.toHaveText("Providers");

    await expect(containedMessages()).resolves.not.toContain("Successfully created provider.");

    await ProvidersListPage.$startWizardButton.click();
    await ProviderWizardView.$wizardTitle.waitForDisplayed();
    await expect(ProviderWizardView.$wizardTitle).resolves.toHaveText("New provider");
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

        await waitFor();
        await ProviderWizardView.$nextButton.click();
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

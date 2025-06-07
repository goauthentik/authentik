import ProviderWizardView from "#tests/pageobjects/provider-wizard.page";
import ProvidersListPage from "#tests/pageobjects/providers-list.page";
import SessionPage from "#tests/pageobjects/session.page";
import { type TestAction, type TestSequence, runTestSequence } from "#tests/utils/controls";
import { ConsoleTestRunner } from "#tests/utils/logger";
import { $, browser, expect } from "@wdio/globals";

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

async function itShouldConfigureASimpleProvider(name: string, providerActions: TestAction[]) {
    return it(`Should successfully configure a ${name} provider`, async () => {
        await reachTheProvider();

        await runTestSequence(providerActions);

        // await ProviderWizardView.$nextButton.click();
        // await providerSuccessMessagePresent();
    });
}

type ProviderTest = [string, TestSequence];

describe("Configuring Providers", async () => {
    const providers: ProviderTest[] = [
        ["Simple OAuth2", simpleOAuth2ProviderForm],
        ["Simple LDAP", simpleLDAPProviderForm],
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
        await itShouldConfigureASimpleProvider(name, provider());
        break;
    }
});

/// <reference types="@wdio/globals/types" />
import { randomId } from "@goauthentik/elements/utils/randomId.js";
import SessionPage from "tests/pageobjects/session.page";

import ApplicationWizardView from "../pageobjects/application-wizard.page.js";
import { ApplicationsListPage } from "../pageobjects/applications-list.page.js";
import { type TestAction, type TestSequence, runTestSequence } from "../utils/controls.js";
import { checkIfElementVisible } from "../utils/selectors.js";
import { waitFor } from "../utils/timers.js";
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

const SUCCESS_MESSAGE = "Your application has been saved";

async function reachTheApplicationsPage() {
    await SessionPage.logout();
    await SessionPage.login();

    await ApplicationsListPage.navigate();
    await waitFor();

    await expect(ApplicationsListPage.$pageHeader).resolves.toBeDisplayed();
    await expect(ApplicationsListPage.$pageHeader).resolves.toHaveText("Applications");
}

async function fillOutTheApplication(title: string) {
    const newPrefix = randomId();

    await ApplicationsListPage.$startWizardButton.click();
    await ApplicationWizardView.$wizardTitle.waitForDisplayed();

    await expect(ApplicationWizardView.$wizardTitle).resolves.toHaveText("New application");

    await ApplicationWizardView.$app.$name.setValue(`${title} - ${newPrefix}`);
    await ApplicationWizardView.$app.$uiSettings.scrollIntoView();
    await ApplicationWizardView.$app.$uiSettings.click();
    await ApplicationWizardView.$app.$launchURL.scrollIntoView();
    await ApplicationWizardView.$app.$launchURL.setValue("http://example.goauthentik.io");
    await ApplicationWizardView.$nextButton.click();
    await waitFor();
}

async function getCommitMessage() {
    await ApplicationWizardView.$successMessage.waitForDisplayed();

    return ApplicationWizardView.$successMessage;
}

async function submitProvider(provider: TestAction[]) {
    // The wizard automagically provides a name. If it doesn't, that's a bug.
    const wizardProvider = provider.filter((p) => p.length < 2 || p[1] !== "name");

    await $(">>>ak-wizard-page-type-create").waitForDisplayed();

    await runTestSequence(wizardProvider);

    await ApplicationWizardView.$nextButton.click();
    await waitFor();
}

async function passByPoliciesAndCommit() {
    const title = await $$(">>>ak-wizard-title").find<WebdriverIO.Element>(checkIfElementVisible);

    // Expect to be on the Bindings panel
    await expect(title.getText()).resolves.toEqual("Configure Policy/User/Group Bindings");

    await ApplicationWizardView.$nextButton.click();
    await waitFor();
    await ApplicationWizardView.$submitPage.waitForDisplayed();
    await ApplicationWizardView.$nextButton.click();

    await expect(getCommitMessage()).resolves.toHaveText(SUCCESS_MESSAGE);
}

async function itShouldConfigureApplicationsViaTheWizard(testName: string, provider: TestAction[]) {
    it(`Should successfully configure an application with a ${testName} provider`, async () => {
        await reachTheApplicationsPage();
        await fillOutTheApplication(testName);
        await submitProvider(provider);
        await passByPoliciesAndCommit();
    });
}

let providers: [testName: string, testSequence: TestSequence][] = [
    ["Simple LDAP", simpleLDAPProviderForm],
    ["Simple OAuth2", simpleOAuth2ProviderForm],
    ["Simple Radius", simpleRadiusProviderForm],
    ["Simple SAML", simpleSAMLProviderForm],
    ["Simple SCIM", simpleSCIMProviderForm],
    ["Simple Proxy", simpleProxyProviderForm],
    ["Simple Forward Auth (single)", simpleForwardAuthProxyProviderForm],
    ["Simple Forward Auth (domain)", simpleForwardAuthDomainProxyProviderForm],
    ["Complete OAuth2", completeOAuth2ProviderForm],
    ["Complete LDAP", completeLDAPProviderForm],
    ["Complete Radius", completeRadiusProviderForm],
    ["Complete SAML", completeSAMLProviderForm],
    ["Complete SCIM", completeSCIMProviderForm],
    ["Complete Proxy", completeProxyProviderForm],
    ["Complete Forward Auth (single)", completeForwardAuthProxyProviderForm],
    ["Complete Forward Auth (domain)", completeForwardAuthDomainProxyProviderForm],
];

if (Date.now()) {
    providers = providers.slice(0, 1);
}

describe("Configuring Applications Via the Wizard", () => {
    for (const [name, provider] of providers) {
        itShouldConfigureApplicationsViaTheWizard(name, provider());
    }
});

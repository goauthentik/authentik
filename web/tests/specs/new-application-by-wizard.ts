import { expect } from "@wdio/globals";

import ApplicationWizardView from "../pageobjects/application-wizard.page.js";
import ApplicationsListPage from "../pageobjects/applications-list.page.js";
import { type TestAction, type TestSequence, runTestSequence } from "../pageobjects/controls.js";
import { checkIfElementVisible, findElement } from "../pageobjects/selectors.js";
import { randomId } from "../utils/index.js";
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

const SUCCESS_MESSAGE = "Your application has been saved";

async function reachTheApplicationsPage() {
    await ApplicationsListPage.logout();
    await login();
    await ApplicationsListPage.open();
    await ApplicationsListPage.pause();
    await expect(ApplicationsListPage.pageHeader()).toBeDisplayed();
    await expect(ApplicationsListPage.pageHeader()).toHaveText("Applications");
}

async function fillOutTheApplication(title: string) {
    const newPrefix = randomId();

    await ApplicationsListPage.startWizardButton().click();
    await ApplicationWizardView.wizardTitle().waitForDisplayed();
    await expect(ApplicationWizardView.wizardTitle()).toHaveText("New application");
    await ApplicationWizardView.app.name().setValue(`${title} - ${newPrefix}`);
    await ApplicationWizardView.app.uiSettings().scrollIntoView();
    await ApplicationWizardView.app.uiSettings().click();
    await ApplicationWizardView.app.launchUrl().scrollIntoView();
    await ApplicationWizardView.app.launchUrl().setValue("http://example.goauthentik.io");
    await ApplicationWizardView.nextButton().click();
    await ApplicationWizardView.pause();
}

async function getCommitMessage() {
    await ApplicationWizardView.successMessage().waitForDisplayed();
    return ApplicationWizardView.successMessage();
}

async function fillOutTheProviderAndProceed(provider: TestAction[]) {
    // The wizard automagically provides a name.  If it doesn't, that's a bug.
    const wizardProvider = provider.filter((p) => p.length < 2 || p[1] !== "name");
    await $(">>>ak-wizard-page-type-create").waitForDisplayed();

    await runTestSequence(wizardProvider);

    await ApplicationWizardView.nextButton().click();
    await ApplicationWizardView.pause();
}

async function passByPoliciesAndCommit() {
    const title = await findElement($$(">>>ak-wizard-title"), checkIfElementVisible);
    // Expect to be on the Bindings panel
    await expect(title.getText()).toEqual("Configure Policy/User/Group Bindings");
    await ApplicationWizardView.nextButton().click();
    await ApplicationWizardView.pause();
    await ApplicationWizardView.submitPage().waitForDisplayed();
    await ApplicationWizardView.nextButton().click();
    await expect(getCommitMessage()).toHaveText(SUCCESS_MESSAGE);
}

async function itShouldConfigureApplicationsViaTheWizard(name: string, provider: TestAction[]) {
    it(`Should successfully configure an application with a ${name} provider`, async () => {
        await reachTheApplicationsPage();
        await fillOutTheApplication(name);
        await fillOutTheProviderAndProceed(provider);
        await passByPoliciesAndCommit();
    });
}

const providers: [string, TestSequence][] = [
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

describe("Configuring Applications Via the Wizard", () => {
    for (const [name, provider] of providers) {
        itShouldConfigureApplicationsViaTheWizard(name, provider());
    }
});

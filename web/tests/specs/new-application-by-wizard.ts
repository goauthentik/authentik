import { randomId } from "#elements/utils/randomId";
import ApplicationWizardView from "#tests/pageobjects/application-wizard.page";
import { ApplicationsListPage } from "#tests/pageobjects/applications-list.page";
import SessionPage from "#tests/pageobjects/session.page";
import {
    type TestAction,
    type TestSequence,
    runTestSequence,
    setTextInput,
    toggleFormGroup,
} from "#tests/utils/controls";
import { ConsoleTestRunner } from "#tests/utils/logger";
import { checkIfElementVisible, findElementsByTestID } from "#tests/utils/selectors";
import { $, expect } from "@wdio/globals";

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
    // await waitFor();

    ConsoleTestRunner.info("Applications Page: Looking for page header...");

    await expect(ApplicationsListPage.$pageHeader).toBeDisplayed();
    await expect(ApplicationsListPage.$pageHeader).toHaveText("Applications");
}

async function fillOutTheApplication(title: string) {
    const newPrefix = randomId();
    ConsoleTestRunner.info(`fillOutTheApplication: "${title}"`);

    await ApplicationsListPage.$startWizardButton.click();
    await ApplicationWizardView.$wizardTitle.waitForDisplayed();

    await expect(ApplicationWizardView.$wizardTitle).toHaveText("New application");

    await setTextInput("name", `${title} - ${newPrefix}`);
    await toggleFormGroup("UI Settings", true);

    if (Date.now()) {
        process.exit(1);
    }

    await setTextInput("metaLaunchUrl", "http://example.goauthentik.io");

    await ApplicationWizardView.$nextButton.click();

    ConsoleTestRunner.info(`fillOutTheApplication: done`);
}

async function getCommitMessage() {
    await ApplicationWizardView.$successMessage.waitForDisplayed();

    return ApplicationWizardView.$successMessage;
}

async function submitProvider(provider: TestAction[]) {
    // The wizard automagically provides a name. If it doesn't, that's a bug.
    const wizardProvider = provider.filter((p) => p.length < 2 || p[1] !== "name");

    await $("ak-wizard-page-type-create").waitForDisplayed();

    await runTestSequence(wizardProvider);

    await ApplicationWizardView.$nextButton.click();
    // await waitFor();
}

async function passByPoliciesAndCommit() {
    const $title =
        await findElementsByTestID("wizard-title").find<WebdriverIO.Element>(checkIfElementVisible);

    // Expect to be on the Bindings panel
    await expect($title.getText()).toEqual("Configure Policy/User/Group Bindings");

    await ApplicationWizardView.$nextButton.click();
    // await waitFor();
    await ApplicationWizardView.$submitPage.waitForDisplayed();
    await ApplicationWizardView.$nextButton.click();

    await expect(getCommitMessage()).toHaveText(SUCCESS_MESSAGE);
}

function itShouldConfigureApplicationsViaTheWizard(testName: string, provider: TestAction[]) {
    it(`Should successfully configure an application with a ${testName} provider`, async () => {
        await reachTheApplicationsPage();
        await fillOutTheApplication(testName);
        await submitProvider(provider);
        await passByPoliciesAndCommit();
    });
}

const providers: [testName: string, testSequence: TestSequence][] = [
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

describe("Configuring Applications Via the Wizard", async () => {
    for (const [name, provider] of providers.slice(0, 1)) {
        itShouldConfigureApplicationsViaTheWizard(name, provider());
    }
});

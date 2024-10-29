// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-nocheck
// ^^^^^^^^^^^ Because TSC cannot handle metaprogramming, and metaprogramming
// via `defineProperties` is how we installed the OUID finders for the various
// wizard types.
import { expect } from "@wdio/globals";

import ApplicationWizardView from "../pageobjects/application-wizard.page.js";
import ApplicationsListPage from "../pageobjects/applications-list.page.js";
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
import { type TestSequence } from "./shared-sequences";

const SUCCESS_MESSAGE = "Your application has been saved";

async function reachTheApplicationsPage() {
    await ApplicationsListPage.logout();
    await login();
    await ApplicationsListPage.open();
    await ApplicationsListPage.pause("ak-page-header");
    await expect(await ApplicationsListPage.pageHeader()).toBeDisplayed();
    await expect(await ApplicationsListPage.pageHeader()).toHaveText("Applications");
}

async function fillOutTheApplication(title: string) {
    const newPrefix = randomId();

    await (await ApplicationsListPage.startWizardButton()).click();
    await (await ApplicationWizardView.wizardTitle()).waitForDisplayed();
    await expect(await ApplicationWizardView.wizardTitle()).toHaveText("New application");
    await (await ApplicationWizardView.app.name()).setValue(`${title} - ${newPrefix}`);
    await (await ApplicationWizardView.app.uiSettings()).scrollIntoView();
    await (await ApplicationWizardView.app.uiSettings()).click();
    await (await ApplicationWizardView.app.launchUrl()).scrollIntoView();
    await (await ApplicationWizardView.app.launchUrl()).setValue("http://example.goauthentik.io");
    await (await ApplicationWizardView.nextButton()).click();
    await ApplicationWizardView.pause();
}

async function getCommitMessage() {
    await (await ApplicationWizardView.successMessage()).waitForDisplayed();
    return await ApplicationWizardView.successMessage();
}

async function fillOutTheProviderAndCommit(provider: TestSequence) {
    // The wizard automagically provides a name.  If it doesn't, that's a bug.
    const wizardProvider = provider.filter((p) => p.length < 2 || p[1] !== "name");
    await $("ak-wizard-page-type-create").waitForDisplayed();
    for await (const field of wizardProvider) {
        const thefunc = field[0];
        const args = field.slice(1);
        console.log(`Running ${args.join(", ")}`);
        // @ts-expect-error "This is a pretty alien call; I'm not surprised Typescript hates it."
        await thefunc.apply($, args);
    }

    await $("ak-wizard-frame").$("footer button.pf-m-primary").click();
    await ApplicationWizardView.pause();
    await expect(await getCommitMessage()).toHaveText(SUCCESS_MESSAGE);
}

async function itShouldConfigureApplicationsViaTheWizard(name: string, provider: TestSequence) {
    it(`Should successfully configure an application with a ${name} provider`, async () => {
        await reachTheApplicationsPage();
        await fillOutTheApplication(name);
        await fillOutTheProviderAndCommit(provider);
    });
}

const providers = [
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

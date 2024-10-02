import ApplicationWizardView from "../pageobjects/application-wizard.page.js";
import ApplicationsListPage from "../pageobjects/applications-list.page.js";
import { randomId } from "../utils/index.js";
import { login } from "../utils/login.js";
import { expect } from "@wdio/globals";

async function reachTheProvider(title: string) {
    const newPrefix = randomId();

    await ApplicationsListPage.logout();
    await login();
    await ApplicationsListPage.open();
    await ApplicationsListPage.pause("ak-page-header");
    await expect(await ApplicationsListPage.pageHeader()).toBeDisplayed();
    await expect(await ApplicationsListPage.pageHeader()).toHaveText("Applications");

    await (await ApplicationsListPage.startWizardButton()).click();
    await (await ApplicationWizardView.wizardTitle()).waitForDisplayed();
    await expect(await ApplicationWizardView.wizardTitle()).toHaveText("New application");

    await (await ApplicationWizardView.app.name()).setValue(`${title} - ${newPrefix}`);
    await (await ApplicationWizardView.app.uiSettings()).scrollIntoView();
    await (await ApplicationWizardView.app.uiSettings()).click();
    await (await ApplicationWizardView.app.launchUrl()).scrollIntoView();
    await (await ApplicationWizardView.app.launchUrl()).setValue("http://example.goauthentik.io");

    await (await ApplicationWizardView.nextButton()).click();
    return await ApplicationWizardView.pause();
}

async function getCommitMessage() {
    await (await ApplicationWizardView.successMessage()).waitForDisplayed();
    return await ApplicationWizardView.successMessage();
}

const SUCCESS_MESSAGE = "Your application has been saved";
const EXPLICIT_CONSENT = "default-provider-authorization-explicit-consent";

describe("Configure Applications with the Application Wizard", () => {
    it("Should configure a simple LDAP Application", async () => {
        await reachTheProvider("New LDAP Application");

        await (await ApplicationWizardView.providerList()).waitForDisplayed();
        await (await ApplicationWizardView.ldapProvider).scrollIntoView();
        await (await ApplicationWizardView.ldapProvider).click();

        await (await ApplicationWizardView.nextButton()).click();
        await ApplicationWizardView.pause();

        await ApplicationWizardView.ldap.setBindFlow("default-authentication-flow");
        await (await ApplicationWizardView.nextButton()).click();
        await ApplicationWizardView.pause();

        await expect(await getCommitMessage()).toHaveText(SUCCESS_MESSAGE);
    });

    it("Should configure a simple Oauth2 Application", async () => {
        await reachTheProvider("New Oauth2 Application");

        await (await ApplicationWizardView.providerList()).waitForDisplayed();
        await (await ApplicationWizardView.oauth2Provider).scrollIntoView();
        await (await ApplicationWizardView.oauth2Provider).click();

        await (await ApplicationWizardView.nextButton()).click();
        await ApplicationWizardView.pause();

        await ApplicationWizardView.oauth.setAuthorizationFlow(EXPLICIT_CONSENT);
        await (await ApplicationWizardView.nextButton()).click();
        await ApplicationWizardView.pause();

        await expect(await getCommitMessage()).toHaveText(SUCCESS_MESSAGE);
    });

    it("Should configure a simple SAML Application", async () => {
        await reachTheProvider("New SAML Application");

        await (await ApplicationWizardView.providerList()).waitForDisplayed();
        await (await ApplicationWizardView.samlProvider).scrollIntoView();
        await (await ApplicationWizardView.samlProvider).click();

        await (await ApplicationWizardView.nextButton()).click();
        await ApplicationWizardView.pause();

        await ApplicationWizardView.saml.setAuthorizationFlow(EXPLICIT_CONSENT);
        await ApplicationWizardView.saml.acsUrl.setValue("http://example.com:8000/");
        await (await ApplicationWizardView.nextButton()).click();
        await ApplicationWizardView.pause();

        await expect(await getCommitMessage()).toHaveText(SUCCESS_MESSAGE);
    });

    it("Should configure a simple SCIM Application", async () => {
        await reachTheProvider("New SCIM Application");

        await (await ApplicationWizardView.providerList()).waitForDisplayed();
        await (await ApplicationWizardView.scimProvider).scrollIntoView();
        await (await ApplicationWizardView.scimProvider).click();

        await (await ApplicationWizardView.nextButton()).click();
        await ApplicationWizardView.pause();

        await ApplicationWizardView.scim.url.setValue("http://example.com:8000/");
        await ApplicationWizardView.scim.token.setValue("a-very-basic-token");
        await (await ApplicationWizardView.nextButton()).click();
        await ApplicationWizardView.pause();

        await expect(await getCommitMessage()).toHaveText(SUCCESS_MESSAGE);
    });

    it("Should configure a simple Radius Application", async () => {
        await reachTheProvider("New Radius Application");

        await (await ApplicationWizardView.providerList()).waitForDisplayed();
        await (await ApplicationWizardView.radiusProvider).scrollIntoView();
        await (await ApplicationWizardView.radiusProvider).click();

        await (await ApplicationWizardView.nextButton()).click();
        await ApplicationWizardView.pause();

        await ApplicationWizardView.radius.setAuthenticationFlow("default-authentication-flow");
        await (await ApplicationWizardView.nextButton()).click();
        await ApplicationWizardView.pause();

        await expect(await getCommitMessage()).toHaveText(SUCCESS_MESSAGE);
    });

    it("Should configure a simple Transparent Proxy Application", async () => {
        await reachTheProvider("New Transparent Proxy Application");

        await (await ApplicationWizardView.providerList()).waitForDisplayed();
        await (await ApplicationWizardView.proxyProviderProxy).scrollIntoView();
        await (await ApplicationWizardView.proxyProviderProxy).click();
        await (await ApplicationWizardView.nextButton()).click();
        await ApplicationWizardView.pause();

        await ApplicationWizardView.transparentProxy.setAuthorizationFlow(EXPLICIT_CONSENT);
        await ApplicationWizardView.transparentProxy.externalHost.setValue(
            "http://external.example.com",
        );
        await ApplicationWizardView.transparentProxy.internalHost.setValue(
            "http://internal.example.com",
        );

        await (await ApplicationWizardView.nextButton()).click();
        await ApplicationWizardView.pause();

        await expect(await getCommitMessage()).toHaveText(SUCCESS_MESSAGE);
    });

    it("Should configure a simple Forward Proxy Application", async () => {
        await reachTheProvider("New Forward Proxy Application");

        await (await ApplicationWizardView.providerList()).waitForDisplayed();
        await (await ApplicationWizardView.proxyProviderForwardsingle).scrollIntoView();
        await (await ApplicationWizardView.proxyProviderForwardsingle).click();
        await (await ApplicationWizardView.nextButton()).click();
        await ApplicationWizardView.pause();

        await ApplicationWizardView.forwardProxy.setAuthorizationFlow(EXPLICIT_CONSENT);
        await ApplicationWizardView.forwardProxy.externalHost.setValue(
            "http://external.example.com",
        );

        await (await ApplicationWizardView.nextButton()).click();
        await ApplicationWizardView.pause();

        await expect(await getCommitMessage()).toHaveText(SUCCESS_MESSAGE);
    });
});

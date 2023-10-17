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
    await expect(await ApplicationsListPage.pageHeader).toHaveText("Applications");

    await ApplicationsListPage.startWizardButton.click();
    await ApplicationWizardView.wizardTitle.waitForDisplayed();
    await expect(await ApplicationWizardView.wizardTitle).toHaveText("New application");

    await ApplicationWizardView.app.name.setValue(`${title} - ${newPrefix}`);
    await ApplicationWizardView.app.uiSettings.scrollIntoView();
    await ApplicationWizardView.app.uiSettings.click();
    await ApplicationWizardView.app.launchUrl.scrollIntoView();
    await ApplicationWizardView.app.launchUrl.setValue("http://example.goauthentik.io");

    await ApplicationWizardView.nextButton.click();
    return await ApplicationWizardView.pause();
}

async function getCommitMessage() {
    await ApplicationWizardView.successMessage.waitForDisplayed();
    return await ApplicationWizardView.successMessage;
}

const SUCCESS_MESSAGE = "Your application has been saved";
const EXPLICIT_CONSENT = "default-provider-authorization-explicit-consent";

describe("Configure Applications with the Application Wizard", () => {
    it("Should configure a simple LDAP Application", async () => {
        await reachTheProvider("New LDAP Application");

        await ApplicationWizardView.providerList.waitForDisplayed();
        await ApplicationWizardView.ldapProvider.scrollIntoView();
        await ApplicationWizardView.ldapProvider.click();

        await ApplicationWizardView.nextButton.click();
        await ApplicationWizardView.pause();

        await ApplicationWizardView.ldap.setBindFlow("default-authentication-flow");
        await ApplicationWizardView.nextButton.click();
        await ApplicationWizardView.pause();

        await expect(getCommitMessage()).toHaveText(SUCCESS_MESSAGE);
    });

    it("Should configure a simple Oauth2 Application", async () => {
        await reachTheProvider("New Oauth2 Application");

        await ApplicationWizardView.providerList.waitForDisplayed();
        await ApplicationWizardView.oauth2Provider.scrollIntoView();
        await ApplicationWizardView.oauth2Provider.click();

        await ApplicationWizardView.nextButton.click();
        await ApplicationWizardView.pause();

        await ApplicationWizardView.oauth.setAuthorizationFlow(EXPLICIT_CONSENT);
        await ApplicationWizardView.nextButton.click();
        await ApplicationWizardView.pause();

        await expect(getCommitMessage()).toHaveText(SUCCESS_MESSAGE);
    });

    it("Should configure a simple SAML Application", async () => {
        await reachTheProvider("New SAML Application");

        await ApplicationWizardView.providerList.waitForDisplayed();
        await ApplicationWizardView.samlProvider.scrollIntoView();
        await ApplicationWizardView.samlProvider.click();

        await ApplicationWizardView.nextButton.click();
        await ApplicationWizardView.pause();

        await ApplicationWizardView.saml.setAuthorizationFlow(EXPLICIT_CONSENT);
        await ApplicationWizardView.saml.acsUrl.setValue("http://example.com:8000/");
        await ApplicationWizardView.nextButton.click();
        await ApplicationWizardView.pause();

        await expect(getCommitMessage()).toHaveText(SUCCESS_MESSAGE);
    });

    it("Should configure a simple SCIM Application", async () => {
        await reachTheProvider("New SCIM Application");

        await ApplicationWizardView.providerList.waitForDisplayed();
        await ApplicationWizardView.scimProvider.scrollIntoView();
        await ApplicationWizardView.scimProvider.click();

        await ApplicationWizardView.nextButton.click();
        await ApplicationWizardView.pause();

        await ApplicationWizardView.scim.url.setValue("http://example.com:8000/");
        await ApplicationWizardView.scim.token.setValue("a-very-basic-token");
        await ApplicationWizardView.nextButton.click();
        await ApplicationWizardView.pause();

        await expect(getCommitMessage()).toHaveText(SUCCESS_MESSAGE);
    });

    it("Should configure a simple Radius Application", async () => {
        await reachTheProvider("New Radius Application");

        await ApplicationWizardView.providerList.waitForDisplayed();
        await ApplicationWizardView.radiusProvider.scrollIntoView();
        await ApplicationWizardView.radiusProvider.click();

        await ApplicationWizardView.nextButton.click();
        await ApplicationWizardView.pause();

        await ApplicationWizardView.radius.setAuthenticationFlow("default-authentication-flow");
        await ApplicationWizardView.nextButton.click();
        await ApplicationWizardView.pause();

        await expect(getCommitMessage()).toHaveText(SUCCESS_MESSAGE);
    });

    it("Should configure a simple Transparent Proxy Application", async () => {
        await reachTheProvider("New Transparent Proxy Application");

        await ApplicationWizardView.providerList.waitForDisplayed();
        await ApplicationWizardView.proxyProviderProxy.scrollIntoView();
        await ApplicationWizardView.proxyProviderProxy.click();
        await ApplicationWizardView.nextButton.click();
        await ApplicationWizardView.pause();

        await ApplicationWizardView.transparentProxy.setAuthorizationFlow(EXPLICIT_CONSENT);
        await ApplicationWizardView.transparentProxy.externalHost.setValue(
            "http://external.example.com",
        );
        await ApplicationWizardView.transparentProxy.internalHost.setValue(
            "http://internal.example.com",
        );

        await ApplicationWizardView.nextButton.click();
        await ApplicationWizardView.pause();

        await expect(getCommitMessage()).toHaveText(SUCCESS_MESSAGE);
    });

    it("Should configure a simple Forward Proxy Application", async () => {
        await reachTheProvider("New Forward Proxy Application");

        await ApplicationWizardView.providerList.waitForDisplayed();
        await ApplicationWizardView.proxyProviderForwardsingle.scrollIntoView();
        await ApplicationWizardView.proxyProviderForwardsingle.click();
        await ApplicationWizardView.nextButton.click();
        await ApplicationWizardView.pause();

        await ApplicationWizardView.forwardProxy.setAuthorizationFlow(EXPLICIT_CONSENT);
        await ApplicationWizardView.forwardProxy.externalHost.setValue(
            "http://external.example.com",
        );

        await ApplicationWizardView.nextButton.click();
        await ApplicationWizardView.pause();

        await expect(getCommitMessage()).toHaveText(SUCCESS_MESSAGE);
    });
});

import { login } from "../utils/login.js";
import { randomId } from "../utils/index.js";
import ApplicationsListPage from "../pageobjects/applications-list.page.js";
import ApplicationWizardView from "../pageobjects/application-wizard.page.js";
import { expect } from "@wdio/globals";

describe("Configure LDAP Application with Wizard", () => {
    it("Should configure a simple LDAP Application", async () => {
        const newPrefix = randomId();

        await login();
        await ApplicationsListPage.open();
        expect(await ApplicationsListPage.pageHeader).toHaveText("Applications");

        await ApplicationsListPage.startWizardButton.click();
        await ApplicationWizardView.wizardTitle.waitForDisplayed();
        expect(await ApplicationWizardView.wizardTitle).toHaveText("New Application");

        await ApplicationWizardView.app.name.setValue(`New LDAP Application - ${newPrefix}`);
        await ApplicationWizardView.nextButton.click();
        await ApplicationWizardView.pause()

        await ApplicationWizardView.providerList.waitForDisplayed();
        await ApplicationWizardView.providerList.$('>>>input[value=ldapprovider]').click();
        await ApplicationWizardView.nextButton.click();
        await ApplicationWizardView.pause()

        await ApplicationWizardView.ldap.setBindFlow('default-authentication-flow');
        await ApplicationWizardView.nextButton.click();
        await ApplicationWizardView.pause()

        await ApplicationWizardView.commitMessage.waitForDisplayed();
        expect(await ApplicationWizardView.commitMessage).toHaveText("Your application has been saved");
    })
});

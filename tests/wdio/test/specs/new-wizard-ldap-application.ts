import { login } from "../utils/login.js";
import { randomId } from "../utils/index.js";
import ApplicationsListPage from "../pageobjects/applications-list.page.js";
import ApplicationsWizardView from "../pageobjects/applications-wizard.page.js";
import ApplicationForm from "../pageobjects/application-form.view.js";
import { expect } from "@wdio/globals";

describe("Log into Authentik", () => {
    it("should login with valid credentials and reach the UserLibrary", () => {
        const newPrefix = randomId();

        await login();
        await ApplicationsListPage.open();
        expect(await ApplicationsListPage.pageHeader).toHaveText("Applications");

        await ApplicationsListPage.startWizardButton.click();
        await ApplicationsWizardView.wizardTitle.toBeVisible();
        expect(await ApplicationsWizardView.wizardTitle).toHaveText("Create Application");

        await ApplicationForm.name.setValue(`New LDAP Application - ${newPrefix}`);
        
});

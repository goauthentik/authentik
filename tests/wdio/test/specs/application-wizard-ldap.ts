import { expect } from "@wdio/globals";
import LoginPage from "../pageobjects/login.page.js";
import UserLibraryPage from "../pageobjects/user-library.page.js";
import AdminOverviewPage from "../pageobjects/admin-overview.page.js";
import ApplicationsListPage from "../pageobjects/applications-list.page.js";
import ApplicationWizard from "../pageobjects/application-wizard.page.js";
import { randomId } from "../utils/index.js";

describe("Configure new Application", () => {
    it("should navigate to the wizard and configure LDAP", async () => {
        const newId = randomId();

        await LoginPage.open();
        await LoginPage.login("ken@goauthentik.io", "eat10bugs");

        expect(await UserLibraryPage.pageHeader).toHaveText("My Applications");
        await UserLibraryPage.goToAdmin();

        expect(await AdminOverviewPage.pageHeader).toHaveText("Welcome, ");
        await AdminOverviewPage.openApplicationsListPage();

        expect(await ApplicationsListPage.pageHeader).toHaveText("Applications");
        ApplicationsListPage.startCreateApplicationWizard();

        await ApplicationWizard.app.name.setValue(`Test application ${newId}`);
        await ApplicationWizard.nextButton.click();
        await (await ApplicationWizard.getProviderType("ldapprovider")).click();
        await ApplicationWizard.nextButton.click();
        await ApplicationWizard.ldap.setBindFlow("default-authentication-flow");
        await ApplicationWizard.nextButton.click();
        await expect(await ApplicationWizard.commitMessage).toHaveText(
            "Your application has been saved"
        );
    });
});

import AdminPage from "./admin.page.js";
import { $ } from "@wdio/globals";

/**
 * sub page containing specific selectors and methods for a specific page
 */
class ApplicationsListPage extends AdminPage {
    /**
     * define selectors using getter methods
     */

    async startWizardButton() {
        return await $("ak-application-wizard").$('button[slot="trigger"]');
    }

    async open() {
        return await super.open("if/admin/#/core/applications");
    }
}

export default new ApplicationsListPage();

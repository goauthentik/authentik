import { $ } from "@wdio/globals";

import AdminPage from "./admin.page.js";

/**
 * sub page containing specific selectors and methods for a specific page
 */
class ApplicationsListPage extends AdminPage {
    /**
     * define selectors using getter methods
     */

    async startWizardButton() {
        return await $('>>>button[data-ouia-component-id="start-application-wizard"]');
    }

    async open() {
        return await super.open("if/admin/#/core/applications");
    }
}

export default new ApplicationsListPage();

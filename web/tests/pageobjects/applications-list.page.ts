import { $ } from "@wdio/globals";

import AdminPage from "./admin.page.js";

/**
 * sub page containing specific selectors and methods for a specific page
 */
class ApplicationsListPage extends AdminPage {
    /**
     * define selectors using getter methods
     */

    startWizardButton() {
        return $('>>>button[data-ouia-component-id="start-application-wizard"]');
    }

    open() {
        return super.open("if/admin/#/core/applications");
    }
}

export default new ApplicationsListPage();

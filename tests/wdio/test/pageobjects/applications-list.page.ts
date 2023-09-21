import { $ } from "@wdio/globals";
import AdminPage from "./admin.page.js";

/**
 * sub page containing specific selectors and methods for a specific page
 */
class ApplicationsListPage extends AdminPage {
    /**
     * define selectors using getter methods
     */

    async startCreateApplicationWizard() {
        await $('>>>ak-wizard-frame button[slot="trigger"]').click();
    }
}

export default new ApplicationsListPage();

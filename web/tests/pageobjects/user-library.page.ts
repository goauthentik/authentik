import { $ } from "@wdio/globals";

import Page from "./page.js";

/**
 * sub page containing specific selectors and methods for a specific page
 */
class UserLibraryPage extends Page {
    /**
     * define selectors using getter methods
     */

    public async pageHeader() {
        return await $('>>>h1[aria-level="1"]');
    }

    public async goToAdmin() {
        await $('>>>a[href="/if/admin"]').click();
        return await $("ak-admin-overview").waitForDisplayed();
    }
}

export default new UserLibraryPage();

import Page from "./page.js";
import { $ } from "@wdio/globals";

/**
 * sub page containing specific selectors and methods for a specific page
 */
class UserLibraryPage extends Page {
    /**
     * define selectors using getter methods
     */

    public get pageHeader() {
        return $('>>>h1[aria-level="1"]');
    }

    public async goToAdmin() {
        await $('>>>a[href="/if/admin"]').click();
        await $(">>>ak-admin-overview").waitForDisplayed();
    }
}

export default new UserLibraryPage();

import AdminPage from "./admin.page.js";
import { $, browser } from "@wdio/globals";
import { Key } from "webdriverio";

/**
 * sub page containing specific selectors and methods for a specific page
 */
class ApplicationsListPage extends AdminPage {
    /**
     * define selectors using getter methods
     */

    get startWizardButton() {
        return $('>>>ak-wizard button[slot="trigger"]');
    }

    get searchInput() {
        return $('>>>ak-table-search input[name="search"]');
    }

    searchButton() {
        return $('>>>ak-table-search button[type="submit"]');
    }

    // Sufficiently esoteric to justify having its own method
    async clickSearchButton() {
        await browser.execute(
            function (searchButton: unknown) {
                (searchButton as HTMLButtonElement).focus();
            },
            await $('>>>ak-table-search button[type="submit"]'),
        );

        return await browser.action("key").down(Key.Enter).up(Key.Enter).perform();
    }

    // Only use after a very precise search.  :-)
    async findProviderRow() {
        return await $(">>>ak-provider-list td a");
    }

    async open() {
        return await super.open("if/admin/#/core/providers");
    }
}

export default new ApplicationsListPage();

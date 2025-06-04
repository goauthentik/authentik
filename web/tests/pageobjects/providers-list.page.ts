import AdminPage from "#tests/pageobjects/admin.page";
import { navigateBrowser } from "#tests/utils/navigation";
import { $, browser } from "@wdio/globals";
import { Key } from "webdriverio";

export abstract class ProvidersListPage extends AdminPage {
    static pathname = "/if/admin/#/core/providers";

    //#region Selectors

    public static get $newProviderButton() {
        return $('ak-wizard button[slot="trigger"]');
    }

    public static get $searchInput() {
        return $('ak-table-search input[name="search"]');
    }

    public static get $searchButton() {
        return $('ak-table-search button[type="submit"]');
    }

    //#endregion

    //#region Specific interactions

    // Sufficiently esoteric to justify having its own method
    public static async clickSearchButton() {
        $('ak-table-search button[type="submit"]').focus();

        return browser.action("key").down(Key.Enter).up(Key.Enter).perform();
    }

    // Only use after a very precise search.  :-)
    public static async findProviderRow() {
        return $("ak-provider-list td a");
    }

    public static async navigate() {
        return navigateBrowser(ProvidersListPage.pathname);
    }

    //#endregion
}

export default ProvidersListPage;

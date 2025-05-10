/// <reference types="@wdio/globals/types" />
import { navigateBrowser } from "tests/utils/navigation";
import { Key } from "webdriverio";

import AdminPage from "./admin.page.js";

export abstract class ApplicationsListPage extends AdminPage {
    //#region Selectors

    public static get $startWizardButton() {
        return $('>>>ak-wizard button[slot="trigger"]');
    }

    public static get $searchInput() {
        return $('>>>ak-table-search input[name="search"]');
    }

    public static get $searchButton() {
        return $('>>>ak-table-search button[type="submit"]');
    }

    //#endregion

    //#region Specific interactions

    // Sufficiently esoteric to justify having its own method
    public static async clickSearchButton() {
        $('>>>ak-table-search button[type="submit"]').focus();

        return browser.action("key").down(Key.Enter).up(Key.Enter).perform();
    }

    // Only use after a very precise search.  :-)
    public static async findProviderRow() {
        return $(">>>ak-provider-list td a");
    }

    public static navigate() {
        return navigateBrowser("/if/admin/#/core/providers");
    }

    //#endregion
}

export default ApplicationsListPage;

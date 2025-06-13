import { $ } from "@wdio/globals";

export abstract class UserLibraryPage {
    public static readonly pathname = "/if/user/#/library";

    public static get $pageHeading() {
        return $('h1[aria-level="1"]');
    }

    public static async navigateToAdminInterface() {
        await $('a[href="/if/admin"]').click();
        await $("ak-admin-overview").waitForDisplayed();
    }
}

export default UserLibraryPage;

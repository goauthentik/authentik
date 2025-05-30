/// <reference types="@wdio/globals/types" />
import { navigateBrowser } from "#tests/utils/navigation";
import { findElementByTestID } from "#tests/utils/selectors";

export abstract class AdminPage {
    public static get $pageHeader() {
        return findElementByTestID("page-header");
    }

    public static async openApplicationsListPage() {
        return navigateBrowser("/if/admin/#/core/applications");
    }
}

export default AdminPage;

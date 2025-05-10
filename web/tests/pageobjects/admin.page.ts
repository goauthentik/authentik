/// <reference types="@wdio/globals/types" />
import { navigateBrowser } from "tests/utils/navigation";

export abstract class AdminPage {
    public static get $pageHeader() {
        return $(">>>ak-page-header").$('>>>slot[name="header"]');
    }

    public static async openApplicationsListPage() {
        return navigateBrowser("/if/admin/#/core/applications");
    }
}

export default AdminPage;

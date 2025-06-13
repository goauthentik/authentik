import { navigateBrowser } from "#tests/utils/navigation";
import { findElementByTestID } from "#tests/utils/selectors";

export abstract class AdminPage {
    public static get $pageHeader() {
        return findElementByTestID("page-navbar-heading");
    }

    public static async openApplicationsListPage() {
        return navigateBrowser("/if/admin/#/core/applications");
    }
}

export default AdminPage;

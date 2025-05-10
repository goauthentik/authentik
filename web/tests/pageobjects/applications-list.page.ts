/// <reference types="@wdio/globals/types" />
import { navigateBrowser } from "../utils/navigation.js";
import AdminPage from "./admin.page.js";

export abstract class ApplicationsListPage extends AdminPage {
    public static navigate() {
        return navigateBrowser("/if/admin/#/core/applications");
    }
    public static get $startWizardButton() {
        return $('>>>button[data-ouia-component-id="start-application-wizard"]');
    }
}

export default ApplicationsListPage;

import AdminPage from "#tests/pageobjects/admin.page";
import { navigateBrowser } from "#tests/utils/navigation";
import { $ } from "@wdio/globals";

export abstract class ApplicationsListPage extends AdminPage {
    public static navigate() {
        return navigateBrowser("/if/admin/#/core/applications");
    }
    public static get $startWizardButton() {
        return $('button[data-ouia-component-id="start-application-wizard"]');
    }
}

export default ApplicationsListPage;

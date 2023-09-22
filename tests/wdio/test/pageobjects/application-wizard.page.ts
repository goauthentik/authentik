import AdminPage from "./admin.page.js";
import ApplicationForm from "./application-form.view.js";
import LdapForm from "./ldap-form.view.js";
import OauthForm from "./oauth-form.view.js";
import { $ } from "@wdio/globals";

/**
 * sub page containing specific selectors and methods for a specific page
 */
class ApplicationWizardView extends AdminPage {
    /**
     * define selectors using getter methods
     */

    ldap = LdapForm;
    oauth = OauthForm;
    app = ApplicationForm;

    get wizardTitle() {
        return $(">>>ak-application-wizard-commit-application h1.pf-c-title");
    }

    get providerList() {
        return $(">>>ak-application-wizard-authentication-method-choice");
    }

    get nextButton() {
        return $(">>>ak-wizard-frame footer button.pf-m-primary");
    }

    async getProviderType(type: string) {
        return await this.providerList.$(`>>>input[value="${type}"]`);
    }

    get commitMessage() {
        return $(">>>ak-application-wizard-commit-application h1.pf-c-title");
    }
}

export default new ApplicationWizardView();

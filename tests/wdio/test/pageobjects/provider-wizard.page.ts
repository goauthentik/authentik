import AdminPage from "./admin.page.js";
import OauthForm from "./forms/oauth.form.js";
import { $ } from "@wdio/globals";

/**
 * sub page containing specific selectors and methods for a specific page
 */

class ProviderWizardView extends AdminPage {
    /**
     * define selectors using getter methods
     */

    oauth = OauthForm;

    get wizardTitle() {
        return $(">>>ak-wizard .pf-c-wizard__header h1.pf-c-title");
    }

    get providerList() {
        return $(">>>ak-provider-wizard-initial");
    }

    get nextButton() {
        return $(">>>ak-wizard footer button.pf-m-primary");
    }

    async getProviderType(type: string) {
        return await this.providerList.$(`>>>input[value="${type}"]`);
    }

    get successMessage() {
        return $('>>>[data-commit-state="success"]');
    }
}

type Pair = [string, string];

// Define a getter for each provider type in the radio button collection.

const providerValues: Pair[] = [["oauth2", "oauth2Provider"]];

providerValues.forEach(([value, name]: Pair) => {
    Object.defineProperties(ProviderWizardView.prototype, {
        [name]: {
            get: function () {
                return this.providerList.$(`>>>input[id="ak-provider-${value}-form"]`);
            },
        },
    });
});

export default new ProviderWizardView();

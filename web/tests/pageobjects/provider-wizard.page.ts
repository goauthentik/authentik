import AdminPage from "#tests/pageobjects/admin.page";
import OAuthForm from "#tests/pageobjects/forms/oauth.form";
import { findElementByTestID } from "#tests/utils/selectors";
import { $ } from "@wdio/globals";

export class ProviderWizardView extends AdminPage {
    public readonly OAuth = OAuthForm;

    public static get $wizardTitle() {
        return findElementByTestID("wizard-title", $("ak-wizard"));
    }

    public static get $providerList() {
        return $("ak-provider-wizard-initial");
    }

    public static get $nextButton() {
        return findElementByTestID("wizard-navigation-next", $("ak-wizard"));
    }

    public static get $cancelButton() {
        return findElementByTestID("wizard-navigation-abort", $("ak-wizard"));
    }

    public static get $successMessage() {
        return $('[data-commit-state="success"]');
    }

    protected static findProviderForm(providerType: string) {
        const selector = `ak-provider-${providerType}-form`;

        return $(selector);
    }

    public static get $OAuth2ProviderForm() {
        return this.findProviderForm("oauth2");
    }
}

export default ProviderWizardView;

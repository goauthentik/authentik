/// <reference types="@wdio/globals/types" />
import AdminPage from "./admin.page.js";
import OAuthForm from "./forms/oauth.form.js";

export class ProviderWizardView extends AdminPage {
    public readonly OAuth = OAuthForm;

    public static get $wizardTitle() {
        return $(">>>ak-wizard .pf-c-wizard__header h1.pf-c-title");
    }

    public static get $providerList() {
        return $(">>>ak-provider-wizard-initial");
    }

    public static get $nextButton() {
        return $(">>>ak-wizard footer button.pf-m-primary");
    }

    public static get $successMessage() {
        return $('>>>[data-commit-state="success"]');
    }

    protected static findProviderForm(providerType: string) {
        const selector = `>>>input[id="ak-provider-${providerType}-form"]`;

        return this.$providerList.$(selector);
    }

    public static get $OAuth2ProviderForm() {
        return this.findProviderForm("oauth2");
    }
}

export default ProviderWizardView;

/// <reference types="@wdio/globals/types" />
import AdminPage from "./admin.page.js";
import ApplicationForm from "./forms/application.form.js";
import ForwardProxyForm from "./forms/forward-proxy.form.js";
import LDAPForm from "./forms/ldap.form.js";
import OAuthForm from "./forms/oauth.form.js";
import RadiusForm from "./forms/radius.form.js";
import SAMLForm from "./forms/saml.form.js";
import SCIMForm from "./forms/scim.form.js";
import TransparentProxyForm from "./forms/transparent-proxy.form.js";

export abstract class ApplicationWizardView extends AdminPage {
    //#region Selectors

    public static readonly LDAP = LDAPForm;
    public static readonly OAuth = OAuthForm;
    public static readonly TransparentProxy = TransparentProxyForm;
    public static readonly ForwardProxy = ForwardProxyForm;
    public static readonly SAML = SAMLForm;
    public static readonly SCIM = SCIMForm;
    public static readonly RADUS = RadiusForm;
    public static readonly $app = ApplicationForm;

    protected static findOUIDComponent(componentName: string) {
        const selector = `>>>div[data-ouid-component-name="${componentName}"]`;

        return this.$providerList.$(selector);
    }

    public static get $OAuth2Provider() {
        return this.findOUIDComponent("oauth2provider");
    }

    public static get $LDAPProvider() {
        return this.findOUIDComponent("ldapprovider");
    }

    public static get $proxyProvider() {
        return this.findOUIDComponent("proxyprovider");
    }

    public static get $RadiusProvider() {
        return this.findOUIDComponent("radiusprovider");
    }

    public static get $SAMLProvider() {
        return this.findOUIDComponent("samlprovider");
    }

    public static get $SCIMProvider() {
        return this.findOUIDComponent("scimprovider");
    }

    public static get $wizardTitle() {
        return $(">>>.pf-c-wizard__title");
    }

    public static get $providerList() {
        return $(">>>ak-application-wizard-provider-choice-step");
    }

    public static get $nextButton() {
        return $('>>>button[data-ouid-button-kind="wizard-next"]');
    }

    public static getProviderType(providerType: string) {
        // Selector split into a variable to avoid Prettier's parser
        // getting caught on the CSS syntax.
        const selector = `>>>input[value="${providerType}"]`;
        return this.$providerList.$(selector);
    }

    public static get $submitPage() {
        return $(">>>ak-application-wizard-submit-step");
    }

    public static get $successMessage() {
        return $('>>>[data-ouid-component-state="submitted"]');
    }

    //#endregion
}

export default ApplicationWizardView;

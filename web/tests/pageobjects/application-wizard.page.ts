import AdminPage from "#tests/pageobjects/admin.page";
import ApplicationForm from "#tests/pageobjects/forms/application.form";
import ForwardProxyForm from "#tests/pageobjects/forms/forward-proxy.form";
import LDAPForm from "#tests/pageobjects/forms/ldap.form";
import OAuthForm from "#tests/pageobjects/forms/oauth.form";
import RadiusForm from "#tests/pageobjects/forms/radius.form";
import SAMLForm from "#tests/pageobjects/forms/saml.form";
import SCIMForm from "#tests/pageobjects/forms/scim.form";
import TransparentProxyForm from "#tests/pageobjects/forms/transparent-proxy.form";
import { findOUIDComponent } from "#tests/utils/selectors";
import { $ } from "@wdio/globals";

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

    public static get $OAuth2Provider() {
        return findOUIDComponent("oauth2provider", this.$providerList);
    }

    public static get $LDAPProvider() {
        return findOUIDComponent("ldapprovider", this.$providerList);
    }

    public static get $proxyProvider() {
        return findOUIDComponent("proxyprovider", this.$providerList);
    }

    public static get $RadiusProvider() {
        return findOUIDComponent("radiusprovider", this.$providerList);
    }

    public static get $SAMLProvider() {
        return findOUIDComponent("samlprovider", this.$providerList);
    }

    public static get $SCIMProvider() {
        return findOUIDComponent("scimprovider", this.$providerList);
    }

    public static get $wizardTitle() {
        return $("[data-test-id='wizard-title']");
    }

    public static get $providerList() {
        return $("ak-application-wizard-provider-choice-step");
    }

    public static get $nextButton() {
        return $('button[data-ouid-button-kind="wizard-next"]');
    }

    public static getProviderType(providerType: string) {
        // Selector split into a variable to avoid Prettier's parser
        // getting caught on the CSS syntax.
        const selector = `input[value="${providerType}"]`;
        return this.$providerList.$(selector);
    }

    public static get $submitPage() {
        return $("ak-application-wizard-submit-step");
    }

    public static get $successMessage() {
        return $('[data-ouid-component-state="submitted"]');
    }

    //#endregion
}

export default ApplicationWizardView;

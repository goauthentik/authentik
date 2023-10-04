import AdminPage from "./admin.page.js";
import ApplicationForm from "./forms/application.form.js";
import ForwardProxyForm from "./forms/forward-proxy.form.js";
import LdapForm from "./forms/ldap.form.js";
import OauthForm from "./forms/oauth.form.js";
import RadiusForm from "./forms/radius.form.js";
import SamlForm from "./forms/saml.form.js";
import ScimForm from "./forms/scim.form.js";
import TransparentProxyForm from "./forms/transparent-proxy.form.js";
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
    transparentProxy = TransparentProxyForm;
    forwardProxy = ForwardProxyForm;
    saml = SamlForm;
    scim = ScimForm;
    radius = RadiusForm;
    app = ApplicationForm;

    get wizardTitle() {
        return $(">>>ak-wizard-frame .pf-c-wizard__header h1.pf-c-title");
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

    get successMessage() {
        return $('>>>[data-commit-state="success"]');
    }
}

type Pair = [string, string];

// Define a getter for each provider type in the radio button collection.

const providerValues: Pair[] = [
    ["oauth2provider", "oauth2Provider"],
    ["ldapprovider", "ldapProvider"],
    ["proxyprovider-proxy", "proxyProviderProxy"],
    ["proxyprovider-forwardsingle", "proxyProviderForwardsingle"],
    ["radiusprovider", "radiusProvider"],
    ["samlprovider", "samlProvider"],
    ["scimprovider", "scimProvider"],
];

providerValues.forEach(([value, name]: Pair) => {
    Object.defineProperties(ApplicationWizardView.prototype, {
        [name]: {
            get: function () {
                return this.providerList.$(`>>>input[value="${value}"]`);
            },
        },
    });
});

export default new ApplicationWizardView();

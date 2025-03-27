import { $ } from "@wdio/globals";

import AdminPage from "./admin.page.js";
import ApplicationForm from "./forms/application.form.js";
import ForwardProxyForm from "./forms/forward-proxy.form.js";
import LdapForm from "./forms/ldap.form.js";
import OauthForm from "./forms/oauth.form.js";
import RadiusForm from "./forms/radius.form.js";
import SamlForm from "./forms/saml.form.js";
import ScimForm from "./forms/scim.form.js";
import TransparentProxyForm from "./forms/transparent-proxy.form.js";

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

    wizardTitle() {
        return $(">>>.pf-c-wizard__title");
    }

    providerList() {
        return $(">>>ak-application-wizard-provider-choice-step");
    }

    nextButton() {
        return $('>>>button[data-ouid-button-kind="wizard-next"]');
    }

    getProviderType(type: string) {
        return this.providerList().$(`>>>input[value="${type}"]`);
    }

    submitPage() {
        return $(">>>ak-application-wizard-submit-step");
    }

    successMessage() {
        return $('>>>[data-ouid-component-state="submitted"]');
    }
}

type Pair = [string, string];

// Define a getter for each provider type in the radio button collection.

const providerValues: Pair[] = [
    ["oauth2provider", "oauth2Provider"],
    ["ldapprovider", "ldapProvider"],
    ["proxyprovider", "proxyProvider"],
    ["radiusprovider", "radiusProvider"],
    ["samlprovider", "samlProvider"],
    ["scimprovider", "scimProvider"],
];

providerValues.forEach(([value, name]: Pair) => {
    Object.defineProperties(ApplicationWizardView.prototype, {
        [name]: {
            get: function (this: ApplicationWizardView) {
                return this.providerList().$(`>>>div[data-ouid-component-name="${value}"]`);
            },
        },
    });
});

export default new ApplicationWizardView();

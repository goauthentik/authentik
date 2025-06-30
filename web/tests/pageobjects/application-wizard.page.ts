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

    async wizardTitle() {
        return await $(">>>.pf-c-wizard__title");
    }

    async providerList() {
        return await $(">>>ak-application-wizard-provider-choice-step");
    }

    async nextButton() {
        return await $('>>>button[data-ouid-button-kind="wizard-next"]');
    }

    async getProviderType(type: string) {
        // @ts-expect-error "TSC does not understand the ChainablePromiseElement type at all."
        return await this.providerList().$(`>>>input[value="${type}"]`);
    }

    async submitPage() {
        return await $(">>>ak-application-wizard-submit-step");
    }

    async successMessage() {
        return await $('>>>[data-ouid-component-state="submitted"]');
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
            get: async function () {
                return await (
                    await this.providerList()
                ).$(`>>>div[data-ouid-component-name="${value}"]`);
            },
        },
    });
});

export default new ApplicationWizardView();

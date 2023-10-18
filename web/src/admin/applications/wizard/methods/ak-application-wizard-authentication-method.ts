import { customElement } from "@lit/reactive-element/decorators/custom-element.js";

import BasePanel from "../BasePanel";
import { providerRendererList } from "../auth-method-choice/ak-application-wizard-authentication-method-choice.choices";
import "./ldap/ak-application-wizard-authentication-by-ldap";
import "./oauth/ak-application-wizard-authentication-by-oauth";
import "./proxy/ak-application-wizard-authentication-for-forward-domain-proxy";
import "./proxy/ak-application-wizard-authentication-for-reverse-proxy";
import "./proxy/ak-application-wizard-authentication-for-single-forward-proxy";
import "./radius/ak-application-wizard-authentication-by-radius";
import "./saml/ak-application-wizard-authentication-by-saml-configuration";
import "./scim/ak-application-wizard-authentication-by-scim";

// prettier-ignore

@customElement("ak-application-wizard-authentication-method")
export class ApplicationWizardApplicationDetails extends BasePanel {
    render() {
        const handler = providerRendererList.get(this.wizard.providerModel);
        if (!handler) {
            throw new Error(
                "Unrecognized authentication method in ak-application-wizard-authentication-method",
            );
        }
        return handler();
    }
}

export default ApplicationWizardApplicationDetails;

import { customElement } from "@lit/reactive-element/decorators/custom-element.js";

import { BasePanel } from "../BasePanel";
import { providerRendererList } from "../provider-choice/ak-application-wizard-provider.choices";
import "./ldap/ak-application-wizard-authentication-by-ldap";
import "./oauth/ak-application-wizard-authentication-by-oauth";
import "./proxy/ak-application-wizard-authentication-for-forward-domain-proxy";
import "./proxy/ak-application-wizard-authentication-for-reverse-proxy";
import "./proxy/ak-application-wizard-authentication-for-single-forward-proxy";
import "./rac/ak-application-wizard-authentication-for-rac";
import "./radius/ak-application-wizard-authentication-by-radius";
import "./saml/ak-application-wizard-authentication-by-saml-configuration";
import "./scim/ak-application-wizard-authentication-by-scim";

@customElement("ak-application-wizard-provider")
export class ApplicationWizardApplicationDetails extends BasePanel {
    render() {
        const handler = providerRendererList.get(this.wizard.providerModel);
        if (!handler) {
            throw new Error("Unrecognized authentication method in ak-application-wizard-provider");
        }
        return handler();
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-provider": ApplicationWizardApplicationDetails;
    }
}

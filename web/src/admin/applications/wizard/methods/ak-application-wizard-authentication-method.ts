import { WizardStep } from "@goauthentik/components/ak-wizard-main/AkWizardStep";
import { WizardButton } from "@goauthentik/components/ak-wizard-main/types";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { html } from "lit";

import BasePanel from "../BasePanel";
import { providerRendererList } from "../auth-method-choice/ak-application-wizard-authentication-method-choice.choices";
import "./ldap/ak-application-wizard-authentication-by-ldap";
import "./oauth/ak-application-wizard-authentication-by-oauth";
import "./proxy/ak-application-wizard-authentication-for-forward-domain-proxy";
import "./proxy/ak-application-wizard-authentication-for-reverse-proxy";
import "./proxy/ak-application-wizard-authentication-for-single-forward-proxy";
import "./rac/ak-application-wizard-authentication-for-rac";
import "./radius/ak-application-wizard-authentication-by-radius";
import "./saml/ak-application-wizard-authentication-by-saml-configuration";
import "./scim/ak-application-wizard-authentication-by-scim";

export class ProviderDetailsStep extends WizardStep {
    id = "provider-details";
    label = msg("Provider Configuration");
    disabled = true;
    valid = false;

    override get buttons(): WizardButton[] {
        return [
            this.valid ? { kind: "next", destination: "submit" } : { kind: "next", disabled: true },
            { kind: "back", destination: "provider-method" },
            { kind: "cancel" },
        ];
    }

    render() {
        return html`<ak-application-wizard-authentication-method
            .step=${this}
        ></ak-application-wizard-authentication-method>`;
    }
}

@customElement("ak-application-wizard-authentication-method")
export class ApplicationWizardApplicationDetails extends BasePanel {
    render() {
        const handler = providerRendererList.get(this.wizard.providerModel);
        if (!handler) {
            throw new Error(
                "Unrecognized authentication method in ak-application-wizard-authentication-method",
            );
        }
        return handler(this.step);
    }
}

export default ApplicationWizardApplicationDetails;

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-authentication-method": ApplicationWizardApplicationDetails;
    }
}

import { consume } from "@lit/context";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";

import BasePanel from "../BasePanel";
import { applicationWizardProvidersContext } from "../ContextIdentity";
import type { LocalTypeCreate } from "./ak-application-wizard-authentication-method-choice.choices";
import "./ldap/ak-application-wizard-authentication-by-ldap";
import "./oauth/ak-application-wizard-authentication-by-oauth";
import "./proxy/ak-application-wizard-authentication-for-reverse-proxy";
import "./rac/ak-application-wizard-authentication-for-rac";
import "./radius/ak-application-wizard-authentication-by-radius";
import "./saml/ak-application-wizard-authentication-by-saml-configuration";
import "./scim/ak-application-wizard-authentication-by-scim";

@customElement("ak-application-wizard-authentication-method")
export class ApplicationWizardApplicationDetails extends BasePanel {
    @consume({ context: applicationWizardProvidersContext })
    public providerModelsList: LocalTypeCreate[];

    render() {
        const handler: LocalTypeCreate | undefined = this.providerModelsList.find(
            ({ modelName }) => modelName === this.wizard.providerModel,
        );
        if (!handler) {
            throw new Error(
                "Unrecognized authentication method in ak-application-wizard-authentication-method",
            );
        }
        return handler.renderer();
    }
}

export default ApplicationWizardApplicationDetails;

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-authentication-method": ApplicationWizardApplicationDetails;
    }
}

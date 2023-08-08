import { customElement } from "@lit/reactive-element/decorators/custom-element.js";

import ApplicationWizardPageBase from "./ApplicationWizardPageBase";
import { providerRendererList } from "./ak-application-wizard-authentication-method-choice.choices";
import "./ldap/ak-application-wizard-authentication-by-ldap";
import "./oauth/ak-application-wizard-authentication-by-oauth";
import "./proxy/ak-application-wizard-authentication-for-reverse-proxy";
import "./proxy/ak-application-wizard-authentication-for-single-forward-proxy";

// prettier-ignore

@customElement("ak-application-wizard-authentication-method")
export class ApplicationWizardApplicationDetails extends ApplicationWizardPageBase {
    render() {
        const handler = providerRendererList.get(this.wizard.providerType);
        if (!handler) {
            throw new Error(
                "Unrecognized authentication method in ak-application-wizard-authentication-method",
            );
        }
        return handler();
    }
}

export default ApplicationWizardApplicationDetails;

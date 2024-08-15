//import { policyOptions } from "@goauthentik/admin/applications/ApplicationForm";
// import { PFSize } from "@goauthentik/common/enums.js";
// import { first } from "@goauthentik/common/utils";
import { PFSize } from "@goauthentik/common/enums.js";
import "@goauthentik/components/ak-radio-input";
import "@goauthentik/components/ak-slug-input";
import "@goauthentik/components/ak-switch-input";
import "@goauthentik/components/ak-text-input";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { html } from "lit";

// import { ifDefined } from "lit/directives/if-defined.js";
import BasePanel from "../BasePanel";

@customElement("ak-application-wizard-policy-bindings")
export class ApplicationWizardPolicyBindings extends BasePanel {
    render() {
        if (this.wizard.policies.length === 0) {
            return html`<ak-empty-state header=${msg("No bound policies.")} icon="pf-icon-module">
                <div slot="body">${msg("No policies are currently bound to this object.")}</div>
                <div slot="primary">
                    <ak-forms-modal size=${PFSize.Medium}>
                        <span slot="submit"> ${msg("Create")} </span>
                        <span slot="header"> ${msg("Create Binding")} </span>
                        <p>Insert static binding form here</p>
                        <button slot="trigger" class="pf-c-button pf-m-primary">
                            ${msg("Bind existing policy/group/user")}
                        </button>
                    </ak-forms-modal>
                </div>
            </ak-empty-state>`;
        }

        return html`<p>Nothing to see here. Move along.</p>`;
    }
}

export default ApplicationWizardPolicyBindings;

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-policy-bindings": ApplicationWizardPolicyBindings;
    }
}

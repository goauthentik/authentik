import "#admin/stages/invitation/wizard/InvitationWizardFlowStep";
import "#admin/stages/invitation/wizard/InvitationWizardDetailsStep";
import "#elements/wizard/Wizard";

import { AKElement } from "#elements/Base";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { html, TemplateResult } from "lit";

import PFButton from "@patternfly/patternfly/components/Button/button.css";

@customElement("ak-invitation-wizard")
export class InvitationWizard extends AKElement {
    static styles = [PFButton];

    render(): TemplateResult {
        return html`
            <ak-wizard
                .steps=${["flow-step", "details-step"]}
                header=${msg("New Invitation")}
                description=${msg("Create a new invitation with an enrollment flow.")}
            >
                <ak-invitation-wizard-flow-step
                    slot="flow-step"
                    label=${msg("Enrollment Flow")}
                ></ak-invitation-wizard-flow-step>
                <ak-invitation-wizard-details-step
                    slot="details-step"
                    label=${msg("Invitation Details")}
                ></ak-invitation-wizard-details-step>
                <button slot="trigger" class="pf-c-button pf-m-primary">
                    ${msg("Create with wizard")}
                </button>
            </ak-wizard>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-invitation-wizard": InvitationWizard;
    }
}

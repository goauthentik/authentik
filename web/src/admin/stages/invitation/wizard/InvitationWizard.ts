import "#admin/stages/invitation/wizard/InvitationWizardDetailsStep";
import "#admin/stages/invitation/wizard/InvitationWizardEmailStep";
import "#admin/stages/invitation/wizard/InvitationWizardFlowStep";
import "#admin/stages/invitation/wizard/InvitationWizardSuccessStep";
import "#elements/wizard/Wizard";

import { AKElement } from "#elements/Base";
import { TransclusionChildElement, TransclusionChildSymbol } from "#elements/dialogs";
import { SlottedTemplateResult } from "#elements/types";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { property } from "@lit/reactive-element/decorators/property.js";
import { html } from "lit";

export type InvitationWizardFlowMode = "existing" | "create";

@customElement("ak-invitation-wizard")
export class InvitationWizard extends AKElement implements TransclusionChildElement {
    public static verboseName = msg("Invitation");

    public [TransclusionChildSymbol] = true;

    @property({ type: String })
    public mode: InvitationWizardFlowMode = "existing";

    protected override createRenderRoot(): HTMLElement | DocumentFragment {
        return this;
    }

    protected override render(): SlottedTemplateResult {
        return html`<ak-wizard
            entity-singular=${msg("Invitation")}
            description=${msg("Create a new invitation with an enrollment flow.")}
            .initialSteps=${["flow-step", "details-step", "success-step"]}
        >
            <ak-invitation-wizard-flow-step
                slot="flow-step"
                headline=${msg("Enrollment Flow")}
                .mode=${this.mode}
            ></ak-invitation-wizard-flow-step>
            <ak-invitation-wizard-details-step
                slot="details-step"
                headline=${msg("Invitation Details")}
            ></ak-invitation-wizard-details-step>
            <ak-invitation-wizard-success-step
                slot="success-step"
                headline=${msg("Invitation Link")}
            ></ak-invitation-wizard-success-step>
            <ak-invitation-wizard-email-step
                slot="email-step"
                headline=${msg("Send via Email")}
            ></ak-invitation-wizard-email-step>
        </ak-wizard>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-invitation-wizard": InvitationWizard;
    }
}

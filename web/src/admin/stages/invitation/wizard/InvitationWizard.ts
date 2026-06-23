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

export const InvitationWizardFlowMode = {
    Existing: "existing",
    Create: "create",
} as const;

export type InvitationWizardFlowMode =
    (typeof InvitationWizardFlowMode)[keyof typeof InvitationWizardFlowMode];

@customElement("ak-invitation-wizard")
export class InvitationWizard extends AKElement implements TransclusionChildElement {
    public static verboseName = msg("Invitation");

    public [TransclusionChildSymbol] = true;

    @property({ type: String })
    public mode: InvitationWizardFlowMode = InvitationWizardFlowMode.Existing;

    protected override createRenderRoot(): HTMLElement | DocumentFragment {
        return this;
    }

    public formatARIALabel(): string {
        return this.mode === InvitationWizardFlowMode.Create
            ? msg("Create New Invitation Wizard", {
                  id: "invitations.wizard.create.ariaLabel",
                  desc: "ARIA label for the invitation wizard when creating a new invitation",
              })
            : msg("Existing Invitation Wizard", {
                  id: "invitations.wizard.existing.ariaLabel",
                  desc: "ARIA label for the invitation wizard when using an existing invitation",
              });
    }

    protected override render(): SlottedTemplateResult {
        return html`<ak-wizard
            verbose-name=${msg("Invitation")}
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

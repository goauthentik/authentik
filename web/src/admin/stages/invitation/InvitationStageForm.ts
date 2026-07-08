import "#components/ak-switch-input";
import "#components/ak-text-input";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";

import { aki } from "#common/api/client";

import { BaseStageForm } from "#admin/stages/BaseStageForm";

import { InvitationStage, StagesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-stage-invitation-form")
export class InvitationStageForm extends BaseStageForm<InvitationStage> {
    public static override verboseName = msg("Invitation Stage");
    public static override verboseNamePlural = msg("Invitation Stages");

    protected endpoints = {
        load: (stageUuid: string) => aki(StagesApi).stagesInvitationStagesRetrieve({ stageUuid }),
        create: (invitationStageRequest: InvitationStage) =>
            aki(StagesApi).stagesInvitationStagesCreate({ invitationStageRequest }),
        update: (stageUuid: string, invitationStageRequest: InvitationStage) =>
            aki(StagesApi).stagesInvitationStagesUpdate({ stageUuid, invitationStageRequest }),
    };

    protected override renderForm(): TemplateResult {
        return html`<ak-text-input
                label=${msg("Stage Name")}
                required
                name="name"
                value="${this.instance?.name || ""}"
                help=${msg("This stage can be included in enrollment flows to accept invitations.")}
                placeholder=${msg("e.g. invitation-stage")}
                input-hint="code"
            ></ak-text-input>
            <ak-switch-input
                name="continueFlowWithoutInvitation"
                label=${msg("Continue flow without invitation")}
                ?checked=${this.instance?.continueFlowWithoutInvitation ?? false}
                help=${msg(
                    "If this flag is set, this Stage will jump to the next Stage when no Invitation is given. By default this Stage will cancel the Flow when no invitation is given.",
                )}
            ></ak-switch-input>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-invitation-form": InvitationStageForm;
    }
}

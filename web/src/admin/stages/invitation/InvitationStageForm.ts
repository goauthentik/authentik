import "#components/ak-switch-input";
import "#components/ak-text-input";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";

import { DEFAULT_CONFIG } from "#common/api/config";

import { BaseStageForm } from "#admin/stages/BaseStageForm";

import { InvitationStage, StagesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-stage-invitation-form")
export class InvitationStageForm extends BaseStageForm<InvitationStage> {
    public static override verboseName = msg("Invitation Stage");
    public static override verboseNamePlural = msg("Invitation Stages");

    protected override loadInstance(pk: string): Promise<InvitationStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesInvitationStagesRetrieve({
            stageUuid: pk,
        });
    }

    protected override async send(data: InvitationStage): Promise<InvitationStage> {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesInvitationStagesUpdate({
                stageUuid: this.instance.pk || "",
                invitationStageRequest: data,
            });
        }
        return new StagesApi(DEFAULT_CONFIG).stagesInvitationStagesCreate({
            invitationStageRequest: data,
        });
    }

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

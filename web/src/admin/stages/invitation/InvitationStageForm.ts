import "#components/ak-switch-input";
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
    loadInstance(pk: string): Promise<InvitationStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesInvitationStagesRetrieve({
            stageUuid: pk,
        });
    }

    async send(data: InvitationStage): Promise<InvitationStage> {
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

    renderForm(): TemplateResult {
        return html` <span>
                ${msg("This stage can be included in enrollment flows to accept invitations.")}
            </span>
            <ak-form-element-horizontal label=${msg("Name")} required name="name">
                <input
                    type="text"
                    value="${this.instance?.name || ""}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-group open label="${msg("Stage-specific settings")}">
                <div class="pf-c-form">
                    <ak-switch-input
                        name="continueFlowWithoutInvitation"
                        label=${msg("Continue flow without invitation")}
                        ?checked=${this.instance?.continueFlowWithoutInvitation ?? false}
                        help=${msg(
                            "If this flag is set, this Stage will jump to the next Stage when no Invitation is given. By default this Stage will cancel the Flow when no invitation is given.",
                        )}
                    ></ak-switch-input>
                </div>
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-invitation-form": InvitationStageForm;
    }
}

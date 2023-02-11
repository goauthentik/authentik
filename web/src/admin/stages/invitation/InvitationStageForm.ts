import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import { InvitationStage, StagesApi } from "@goauthentik/api";

@customElement("ak-stage-invitation-form")
export class InvitationStageForm extends ModelForm<InvitationStage, string> {
    loadInstance(pk: string): Promise<InvitationStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesInvitationStagesRetrieve({
            stageUuid: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated stage.`;
        } else {
            return t`Successfully created stage.`;
        }
    }

    send = (data: InvitationStage): Promise<InvitationStage> => {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesInvitationStagesUpdate({
                stageUuid: this.instance.pk || "",
                invitationStageRequest: data,
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesInvitationStagesCreate({
                invitationStageRequest: data,
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <div class="form-help-text">
                ${t`This stage can be included in enrollment flows to accept invitations.`}
            </div>
            <ak-form-element-horizontal label=${t`Name`} ?required=${true} name="name">
                <input
                    type="text"
                    value="${this.instance?.name || ""}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header"> ${t`Stage-specific settings`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal name="continueFlowWithoutInvitation">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${first(
                                    this.instance?.continueFlowWithoutInvitation,
                                    true,
                                )}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label"
                                >${t`Continue flow without invitation`}</span
                            >
                        </label>
                        <p class="pf-c-form__helper-text">
                            ${t`If this flag is set, this Stage will jump to the next Stage when no Invitation is given. By default this Stage will cancel the Flow when no invitation is given.`}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}

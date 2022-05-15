import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import { StagesApi, UserLoginStage } from "@goauthentik/api";

import { DEFAULT_CONFIG } from "../../../api/Config";
import "../../../elements/forms/FormGroup";
import "../../../elements/forms/HorizontalFormElement";
import { ModelForm } from "../../../elements/forms/ModelForm";
import "../../../elements/utils/TimeDeltaHelp";
import { first } from "../../../utils";

@customElement("ak-stage-user-login-form")
export class UserLoginStageForm extends ModelForm<UserLoginStage, string> {
    loadInstance(pk: string): Promise<UserLoginStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesUserLoginRetrieve({
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

    send = (data: UserLoginStage): Promise<UserLoginStage> => {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesUserLoginUpdate({
                stageUuid: this.instance.pk || "",
                userLoginStageRequest: data,
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesUserLoginCreate({
                userLoginStageRequest: data,
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <div class="form-help-text">${t`Log the currently pending user in.`}</div>
            <ak-form-element-horizontal label=${t`Name`} ?required=${true} name="name">
                <input
                    type="text"
                    value="${first(this.instance?.name, "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header"> ${t`Stage-specific settings`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${t`Session duration`}
                        ?required=${true}
                        name="sessionDuration"
                    >
                        <input
                            type="text"
                            value="${first(this.instance?.sessionDuration, "seconds=0")}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`Determines how long a session lasts. Default of 0 seconds means that the sessions lasts until the browser is closed.`}
                        </p>
                        <ak-utils-time-delta-help></ak-utils-time-delta-help>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}

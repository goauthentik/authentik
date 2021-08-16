import { UserDeleteStage, StagesApi } from "authentik-api";
import { t } from "@lingui/macro";
import { customElement } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../../elements/forms/HorizontalFormElement";
import { ModelForm } from "../../../elements/forms/ModelForm";

@customElement("ak-stage-user-delete-form")
export class UserDeleteStageForm extends ModelForm<UserDeleteStage, string> {
    loadInstance(pk: string): Promise<UserDeleteStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesUserDeleteRetrieve({
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

    send = (data: UserDeleteStage): Promise<UserDeleteStage> => {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesUserDeleteUpdate({
                stageUuid: this.instance.pk || "",
                userDeleteStageRequest: data,
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesUserDeleteCreate({
                userDeleteStageRequest: data,
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <div class="form-help-text">
                ${t`Delete the currently pending user. CAUTION, this stage does not ask for
                confirmation. Use a consent stage to ensure the user is aware of their actions.`}
            </div>
            <ak-form-element-horizontal label=${t`Name`} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name || "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
        </form>`;
    }
}

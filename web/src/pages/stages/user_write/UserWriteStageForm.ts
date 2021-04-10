import { UserWriteStage, StagesApi } from "authentik-api";
import { t } from "@lingui/macro";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { Form } from "../../../elements/forms/Form";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../../elements/forms/HorizontalFormElement";

@customElement("ak-stage-user-write-form")
export class UserWriteStageForm extends Form<UserWriteStage> {

    set stageUUID(value: string) {
        new StagesApi(DEFAULT_CONFIG).stagesUserWriteRead({
            stageUuid: value,
        }).then(stage => {
            this.stage = stage;
        });
    }

    @property({attribute: false})
    stage?: UserWriteStage;

    getSuccessMessage(): string {
        if (this.stage) {
            return t`Successfully updated stage.`;
        } else {
            return t`Successfully created stage.`;
        }
    }

    send = (data: UserWriteStage): Promise<UserWriteStage> => {
        if (this.stage) {
            return new StagesApi(DEFAULT_CONFIG).stagesUserWriteUpdate({
                stageUuid: this.stage.pk || "",
                data: data
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesUserWriteCreate({
                data: data
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <div class="form-help-text">
                ${t`Write any data from the flow's context's 'prompt_data' to the currently pending user. If no user
                is pending, a new user is created, and data is written to them.`}
            </div>
            <ak-form-element-horizontal
                label=${t`Name`}
                ?required=${true}
                name="name">
                <input type="text" value="${ifDefined(this.stage?.name || "")}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
        </form>`;
    }

}

import { DenyStage, StagesApi } from "authentik-api";
import { t } from "@lingui/macro";
import { customElement } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../../elements/forms/HorizontalFormElement";
import { ModelForm } from "../../../elements/forms/ModelForm";

@customElement("ak-stage-deny-form")
export class DenyStageForm extends ModelForm<DenyStage, string> {
    loadInstance(pk: string): Promise<DenyStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesDenyRetrieve({
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

    send = (data: DenyStage): Promise<DenyStage> => {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesDenyUpdate({
                stageUuid: this.instance.pk || "",
                denyStageRequest: data,
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesDenyCreate({
                denyStageRequest: data,
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <div class="form-help-text">
                ${t`Statically deny the flow. To use this stage effectively, disable *Evaluate on plan* on the respective binding.`}
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

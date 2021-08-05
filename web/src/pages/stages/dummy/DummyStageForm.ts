import { DummyStage, StagesApi } from "authentik-api";
import { t } from "@lingui/macro";
import { customElement } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../../elements/forms/HorizontalFormElement";
import { ModelForm } from "../../../elements/forms/ModelForm";

@customElement("ak-stage-dummy-form")
export class DummyStageForm extends ModelForm<DummyStage, string> {
    loadInstance(pk: string): Promise<DummyStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesDummyRetrieve({
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

    send = (data: DummyStage): Promise<DummyStage> => {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesDummyUpdate({
                stageUuid: this.instance.pk || "",
                dummyStageRequest: data,
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesDummyCreate({
                dummyStageRequest: data,
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <div class="form-help-text">
                ${t`Dummy stage used for testing. Shows a simple continue button and always passes.`}
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

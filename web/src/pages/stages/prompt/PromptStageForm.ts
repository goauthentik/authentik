import { PoliciesApi, PromptStage, StagesApi } from "authentik-api";
import { gettext } from "django";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { Form } from "../../../elements/forms/Form";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../../elements/forms/HorizontalFormElement";
import "../../../elements/forms/FormGroup";
import { until } from "lit-html/directives/until";

@customElement("ak-stage-prompt-form")
export class PromptStageForm extends Form<PromptStage> {

    set stageUUID(value: string) {
        new StagesApi(DEFAULT_CONFIG).stagesPromptStagesRead({
            stageUuid: value,
        }).then(stage => {
            this.stage = stage;
        });
    }

    @property({attribute: false})
    stage?: PromptStage;

    getSuccessMessage(): string {
        if (this.stage) {
            return gettext("Successfully updated stage.");
        } else {
            return gettext("Successfully created stage.");
        }
    }

    send = (data: PromptStage): Promise<PromptStage> => {
        if (this.stage) {
            return new StagesApi(DEFAULT_CONFIG).stagesPromptStagesUpdate({
                stageUuid: this.stage.pk || "",
                data: data
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesPromptStagesCreate({
                data: data
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                label=${gettext("Name")}
                ?required=${true}
                name="name">
                <input type="text" value="${ifDefined(this.stage?.name || "")}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header">
                    ${gettext("Stage-specific settings")}
                </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${gettext("Fields")}
                        ?required=${true}
                        name="fields">
                        <select name="users" class="pf-c-form-control" multiple>
                            ${until(new StagesApi(DEFAULT_CONFIG).stagesPromptPromptsList({
                                ordering: "field_name"
                            }).then(prompts => {
                                return prompts.results.map(prompt => {
                                    const selected = Array.from(this.stage?.fields || []).some(su => {
                                        return su == prompt.pk;
                                    });
                                    return html`<option value=${ifDefined(prompt.pk)} ?selected=${selected}>
                                        ${gettext(`${prompt.fieldKey} ('${prompt.label}', Type ${prompt.type})`)}
                                    </option>`;
                                });
                            }))}
                        </select>
                        <p class="pf-c-form__helper-text">${gettext("Hold control/command to select multiple items.")}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${gettext("Validation Policies")}
                        name="validationPolicies">
                        <select name="users" class="pf-c-form-control" multiple>
                            ${until(new PoliciesApi(DEFAULT_CONFIG).policiesAllList({
                                ordering: "name"
                            }).then(policies => {
                                return policies.results.map(policy => {
                                    const selected = Array.from(this.stage?.validationPolicies || []).some(su => {
                                        return su == policy.pk;
                                    });
                                    return html`<option value=${ifDefined(policy.pk)} ?selected=${selected}>
                                        ${gettext(`${policy.name} (${policy.verboseName})`)}
                                    </option>`;
                                });
                            }))}
                        </select>
                        <p class="pf-c-form__helper-text">${gettext("Selected policies are executed when the stage is submitted to validate the data.")}</p>
                        <p class="pf-c-form__helper-text">${gettext("Hold control/command to select multiple items.")}</p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }

}

import "#admin/stages/prompt/PromptForm";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#elements/forms/FormGroup";
import "#components/ak-text-input";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/ModalForm";

import {
    policiesProvider,
    policiesSelector,
    promptFieldsProvider,
    promptFieldsSelector,
} from "./PromptStageFormHelpers.js";

import { aki } from "#common/api/client";
import { PFSize } from "#common/enums";

import { BaseStageForm } from "#admin/stages/BaseStageForm";

import { PromptStage, StagesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-stage-prompt-form")
export class PromptStageForm extends BaseStageForm<PromptStage> {
    protected endpoints = {
        load: (stageUuid: string) => aki(StagesApi).stagesPromptStagesRetrieve({ stageUuid }),
        create: (promptStageRequest: PromptStage) =>
            aki(StagesApi).stagesPromptStagesCreate({ promptStageRequest }),
        update: (stageUuid: string, promptStageRequest: PromptStage) =>
            aki(StagesApi).stagesPromptStagesUpdate({ stageUuid, promptStageRequest }),
    };

    protected override renderForm(): TemplateResult {
        return html`<p>
                ${msg(
                    html`Show arbitrary input fields to the user, for example during enrollment.
                        Data is saved in the flow context under the
                        <code class="ak-m-code-emphasis">prompt_data</code> variable.`,
                )}
            </p>
            <ak-text-input
                label=${msg("Stage Name")}
                required
                name="name"
                value=${this.instance?.name || ""}
                placeholder=${msg("Type a name for this stage...")}
                ?autofocus=${!this.instance}
            ></ak-text-input>
            <ak-form-group open label="${msg("Stage-specific settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal label=${msg("Fields")} required name="fields">
                        <ak-dual-select-dynamic-selected
                            .provider=${promptFieldsProvider}
                            .selector=${promptFieldsSelector(this.instance?.fields)}
                            available-label="${msg("Available Fields")}"
                            selected-label="${msg("Selected Fields")}"
                        ></ak-dual-select-dynamic-selected>
                        ${this.instance
                            ? html`<ak-forms-modal size=${PFSize.XLarge}>
                                  <span slot="submit">${msg("Create")}</span>
                                  <span slot="header">${msg("Create Prompt")}</span>
                                  <ak-prompt-form slot="form"> </ak-prompt-form>
                                  <button
                                      type="button"
                                      slot="trigger"
                                      class="pf-c-button pf-m-primary"
                                  >
                                      ${msg("Create")}
                                  </button>
                              </ak-forms-modal>`
                            : nothing}
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Validation Policies")}
                        name="validationPolicies"
                    >
                        <ak-dual-select-dynamic-selected
                            .provider=${policiesProvider}
                            .selector=${policiesSelector(this.instance?.validationPolicies)}
                            available-label="${msg("Available Policies")}"
                            selected-label="${msg("Selected Policies")}"
                        ></ak-dual-select-dynamic-selected>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Selected policies are executed when the stage is submitted to validate the data.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-prompt-form": PromptStageForm;
    }
}

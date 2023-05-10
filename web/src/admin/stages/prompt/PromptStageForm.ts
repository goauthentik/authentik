import "@goauthentik/admin/stages/prompt/PromptForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/ModalForm";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    PaginatedPolicyList,
    PaginatedPromptList,
    PoliciesApi,
    PromptStage,
    StagesApi,
} from "@goauthentik/api";

@customElement("ak-stage-prompt-form")
export class PromptStageForm extends ModelForm<PromptStage, string> {
    loadInstance(pk: string): Promise<PromptStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesPromptStagesRetrieve({
            stageUuid: pk,
        });
    }

    async load(): Promise<void> {
        this.prompts = await new StagesApi(DEFAULT_CONFIG).stagesPromptPromptsList({
            ordering: "field_name",
        });
        this.policies = await new PoliciesApi(DEFAULT_CONFIG).policiesAllList({
            ordering: "name",
        });
    }

    prompts?: PaginatedPromptList;
    policies?: PaginatedPolicyList;

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated stage.`;
        } else {
            return t`Successfully created stage.`;
        }
    }

    async send(data: PromptStage): Promise<PromptStage> {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesPromptStagesUpdate({
                stageUuid: this.instance.pk || "",
                promptStageRequest: data,
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesPromptStagesCreate({
                promptStageRequest: data,
            });
        }
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <div class="form-help-text">
                ${t`Show arbitrary input fields to the user, for example during enrollment. Data is saved in the flow context under the 'prompt_data' variable.`}
            </div>
            <ak-form-element-horizontal label=${t`Name`} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name || "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header"> ${t`Stage-specific settings`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal label=${t`Fields`} ?required=${true} name="fields">
                        <select name="users" class="pf-c-form-control" multiple>
                            ${this.prompts?.results.map((prompt) => {
                                const selected = Array.from(this.instance?.fields || []).some(
                                    (su) => {
                                        return su == prompt.pk;
                                    },
                                );
                                return html`<option
                                    value=${ifDefined(prompt.pk)}
                                    ?selected=${selected}
                                >
                                    ${t`${prompt.name} ("${prompt.fieldKey}", of type ${prompt.type})`}
                                </option>`;
                            })}
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${t`Hold control/command to select multiple items.`}
                        </p>
                        ${this.instance
                            ? html`<ak-forms-modal>
                                  <span slot="submit"> ${t`Create`} </span>
                                  <span slot="header"> ${t`Create Prompt`} </span>
                                  <ak-prompt-form slot="form"> </ak-prompt-form>
                                  <button
                                      type="button"
                                      slot="trigger"
                                      class="pf-c-button pf-m-primary"
                                  >
                                      ${t`Create`}
                                  </button>
                              </ak-forms-modal>`
                            : html``}
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Validation Policies`}
                        name="validationPolicies"
                    >
                        <select name="users" class="pf-c-form-control" multiple>
                            ${this.policies?.results.map((policy) => {
                                const selected = Array.from(
                                    this.instance?.validationPolicies || [],
                                ).some((su) => {
                                    return su == policy.pk;
                                });
                                return html`<option
                                    value=${ifDefined(policy.pk)}
                                    ?selected=${selected}
                                >
                                    ${t`${policy.name} (${policy.verboseName})`}
                                </option>`;
                            })}
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${t`Selected policies are executed when the stage is submitted to validate the data.`}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${t`Hold control/command to select multiple items.`}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}

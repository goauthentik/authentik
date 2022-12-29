import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first, groupBy } from "@goauthentik/common/utils";
import "@goauthentik/elements/SearchSelect";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import {
    FlowStageBinding,
    FlowsApi,
    InvalidResponseActionEnum,
    PolicyEngineMode,
    Stage,
    StagesAllListRequest,
    StagesApi,
} from "@goauthentik/api";

@customElement("ak-stage-binding-form")
export class StageBindingForm extends ModelForm<FlowStageBinding, string> {
    loadInstance(pk: string): Promise<FlowStageBinding> {
        return new FlowsApi(DEFAULT_CONFIG).flowsBindingsRetrieve({
            fsbUuid: pk,
        });
    }

    @property()
    targetPk?: string;

    getSuccessMessage(): string {
        if (this.instance?.pk) {
            return t`Successfully updated binding.`;
        } else {
            return t`Successfully created binding.`;
        }
    }

    send = (data: FlowStageBinding): Promise<FlowStageBinding> => {
        if (this.instance?.pk) {
            return new FlowsApi(DEFAULT_CONFIG).flowsBindingsUpdate({
                fsbUuid: this.instance.pk,
                flowStageBindingRequest: data,
            });
        } else {
            return new FlowsApi(DEFAULT_CONFIG).flowsBindingsCreate({
                flowStageBindingRequest: data,
            });
        }
    };

    async getOrder(): Promise<number> {
        if (this.instance?.pk) {
            return this.instance.order;
        }
        const bindings = await new FlowsApi(DEFAULT_CONFIG).flowsBindingsList({
            target: this.targetPk || "",
        });
        const orders = bindings.results.map((binding) => binding.order);
        if (orders.length < 1) {
            return 0;
        }
        return Math.max(...orders) + 1;
    }

    renderTarget(): TemplateResult {
        if (this.instance?.target || this.targetPk) {
            return html`
                <input
                    required
                    name="target"
                    type="hidden"
                    value=${ifDefined(this.instance?.target || this.targetPk)}
                />
            `;
        }
        return html`<ak-form-element-horizontal label=${t`Target`} ?required=${true} name="target">
            <select class="pf-c-form-control">
                ${until(
                    new FlowsApi(DEFAULT_CONFIG)
                        .flowsInstancesList({
                            ordering: "slug",
                        })
                        .then((flows) => {
                            return flows.results.map((flow) => {
                                // No ?selected check here, as this input isn't shown on update forms
                                return html`<option value=${ifDefined(flow.pk)}>
                                    ${flow.name} (${flow.slug})
                                </option>`;
                            });
                        }),
                    html`<option>${t`Loading...`}</option>`,
                )}
            </select>
        </ak-form-element-horizontal>`;
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            ${this.renderTarget()}
            <ak-form-element-horizontal label=${t`Stage`} ?required=${true} name="stage">
                <ak-search-select
                    .fetchObjects=${async (query?: string): Promise<Stage[]> => {
                        const args: StagesAllListRequest = {
                            ordering: "name",
                        };
                        if (query !== undefined) {
                            args.search = query;
                        }
                        const stages = await new StagesApi(DEFAULT_CONFIG).stagesAllList(args);
                        return stages.results;
                    }}
                    .groupBy=${(items: Stage[]) => {
                        return groupBy(items, (stage) => stage.verboseNamePlural);
                    }}
                    .renderElement=${(stage: Stage): string => {
                        return stage.name;
                    }}
                    .value=${(stage: Stage | undefined): string | undefined => {
                        return stage?.pk;
                    }}
                    .selected=${(stage: Stage): boolean => {
                        return stage.pk === this.instance?.stage;
                    }}
                >
                </ak-search-select>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Order`} ?required=${true} name="order">
                <!-- @ts-ignore -->
                <input
                    type="number"
                    value="${until(this.getOrder())}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="evaluateOnPlan">
                <div class="pf-c-check">
                    <input
                        type="checkbox"
                        class="pf-c-check__input"
                        ?checked=${first(this.instance?.evaluateOnPlan, true)}
                    />
                    <label class="pf-c-check__label"> ${t`Evaluate on plan`} </label>
                </div>
                <p class="pf-c-form__helper-text">
                    ${t`Evaluate policies during the Flow planning process. Disable this for input-based policies. Should be used in conjunction with 'Re-evaluate policies', as with both options disabled, policies are **not** evaluated.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="reEvaluatePolicies">
                <div class="pf-c-check">
                    <input
                        type="checkbox"
                        class="pf-c-check__input"
                        ?checked=${first(this.instance?.reEvaluatePolicies, false)}
                    />
                    <label class="pf-c-check__label"> ${t`Re-evaluate policies`} </label>
                </div>
                <p class="pf-c-form__helper-text">
                    ${t`Evaluate policies before the Stage is present to the user.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Invalid response action`}
                ?required=${true}
                name="invalidResponseAction"
            >
                <select class="pf-c-form-control">
                    <option
                        value=${InvalidResponseActionEnum.Retry}
                        ?selected=${this.instance?.invalidResponseAction ===
                        InvalidResponseActionEnum.Retry}
                    >
                        ${t`RETRY returns the error message and a similar challenge to the executor.`}
                    </option>
                    <option
                        value=${InvalidResponseActionEnum.Restart}
                        ?selected=${this.instance?.invalidResponseAction ===
                        InvalidResponseActionEnum.Restart}
                    >
                        ${t`RESTART restarts the flow from the beginning.`}
                    </option>
                    <option
                        value=${InvalidResponseActionEnum.RestartWithContext}
                        ?selected=${this.instance?.invalidResponseAction ===
                        InvalidResponseActionEnum.RestartWithContext}
                    >
                        ${t`RESTART_WITH_CONTEXT restarts the flow from the beginning, while keeping the flow context.`}
                    </option>
                </select>
                <p class="pf-c-form__helper-text">
                    ${t`Configure how the flow executor should handle an invalid response to a challenge.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Policy engine mode`}
                ?required=${true}
                name="policyEngineMode"
            >
                <select class="pf-c-form-control">
                    <option
                        value=${PolicyEngineMode.Any}
                        ?selected=${this.instance?.policyEngineMode === PolicyEngineMode.Any}
                    >
                        ${t`ANY, any policy must match to include this stage access.`}
                    </option>
                    <option
                        value=${PolicyEngineMode.All}
                        ?selected=${this.instance?.policyEngineMode === PolicyEngineMode.All}
                    >
                        ${t`ALL, all policies must match to include this stage access.`}
                    </option>
                </select>
            </ak-form-element-horizontal>
        </form>`;
    }
}

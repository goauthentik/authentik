import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first, groupBy } from "@goauthentik/common/utils";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/forms/SearchSelect";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import {
    FlowStageBinding,
    FlowsApi,
    FlowsInstancesListDesignationEnum,
    InvalidResponseActionEnum,
    PolicyEngineMode,
    Stage,
    StagesAllListRequest,
    StagesApi,
} from "@goauthentik/api";

@customElement("ak-stage-binding-form")
export class StageBindingForm extends ModelForm<FlowStageBinding, string> {
    async loadInstance(pk: string): Promise<FlowStageBinding> {
        const binding = await new FlowsApi(DEFAULT_CONFIG).flowsBindingsRetrieve({
            fsbUuid: pk,
        });
        this.defaultOrder = await this.getOrder();
        return binding;
    }

    @property()
    targetPk?: string;

    @state()
    defaultOrder = 0;

    getSuccessMessage(): string {
        if (this.instance?.pk) {
            return msg("Successfully updated binding.");
        } else {
            return msg("Successfully created binding.");
        }
    }

    send(data: FlowStageBinding): Promise<unknown> {
        if (this.instance?.pk) {
            return new FlowsApi(DEFAULT_CONFIG).flowsBindingsPartialUpdate({
                fsbUuid: this.instance.pk,
                patchedFlowStageBindingRequest: data,
            });
        } else {
            if (this.targetPk) {
                data.target = this.targetPk;
            }
            return new FlowsApi(DEFAULT_CONFIG).flowsBindingsCreate({
                flowStageBindingRequest: data,
            });
        }
    }

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
            return html``;
        }
        return html`<ak-form-element-horizontal
            label=${msg("Target")}
            ?required=${true}
            name="target"
        >
            <ak-flow-search
                flowType=${FlowsInstancesListDesignationEnum.Authorization}
                .currentFlow=${this.instance?.target}
                required
            ></ak-flow-search>
        </ak-form-element-horizontal>`;
    }

    renderForm(): TemplateResult {
        return html` ${this.renderTarget()}
            <ak-form-element-horizontal label=${msg("Stage")} ?required=${true} name="stage">
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
            <ak-form-element-horizontal label=${msg("Order")} ?required=${true} name="order">
                <input
                    type="number"
                    value="${first(this.instance?.order, this.defaultOrder)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="evaluateOnPlan">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${first(this.instance?.evaluateOnPlan, false)}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${msg("Evaluate when flow is planned")}</span>
                </label>
                <p class="pf-c-form__helper-text">
                    ${msg("Evaluate policies during the Flow planning process.")}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="reEvaluatePolicies">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${first(this.instance?.reEvaluatePolicies, true)}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${msg("Evaluate when stage is run")}</span>
                </label>
                <p class="pf-c-form__helper-text">
                    ${msg("Evaluate policies before the Stage is present to the user.")}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Invalid response behavior")}
                ?required=${true}
                name="invalidResponseAction"
            >
                <ak-radio
                    .options=${[
                        {
                            label: "RETRY",
                            value: InvalidResponseActionEnum.Retry,
                            default: true,
                            description: html`${msg(
                                "Returns the error message and a similar challenge to the executor",
                            )}`,
                        },
                        {
                            label: "RESTART",
                            value: InvalidResponseActionEnum.Restart,
                            description: html`${msg("Restarts the flow from the beginning")}`,
                        },
                        {
                            label: "RESTART_WITH_CONTEXT",
                            value: InvalidResponseActionEnum.RestartWithContext,
                            description: html`${msg(
                                "Restarts the flow from the beginning, while keeping the flow context",
                            )}`,
                        },
                    ]}
                    .value=${this.instance?.invalidResponseAction}
                >
                </ak-radio>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Configure how the flow executor should handle an invalid response to a challenge given by this bound stage.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Policy engine mode")}
                ?required=${true}
                name="policyEngineMode"
            >
                <ak-radio
                    .options=${[
                        {
                            label: "any",
                            value: PolicyEngineMode.Any,
                            default: true,
                            description: html`${msg("Any policy must match to grant access")}`,
                        },
                        {
                            label: "all",
                            value: PolicyEngineMode.All,
                            description: html`${msg("All policies must match to grant access")}`,
                        },
                    ]}
                    .value=${this.instance?.policyEngineMode}
                >
                </ak-radio>
            </ak-form-element-horizontal>`;
    }
}

import "#components/ak-switch-input";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import { aki } from "#common/api/client";
import { groupBy } from "#common/utils";

import { ModelForm } from "#elements/forms/ModelForm";
import { RadioOption } from "#elements/forms/Radio";
import { SearchSelectSource, withQuery } from "#elements/forms/SearchSelect/shared";
import { SlottedTemplateResult } from "#elements/types";

import { AKLabel } from "#components/ak-label";
import { AKSearchSelect } from "#components/ak-search-select-field";

import { AKFlowSearch } from "#admin/common/ak-flow-search/AKFlowSearch";
import { policyEngineModes } from "#admin/policies/PolicyEngineModes";

import {
    FlowDesignationEnum,
    FlowsApi,
    FlowStageBinding,
    InvalidResponseActionEnum,
    Stage,
    StagesApi,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";

const stageSource: SearchSelectSource<Stage> = {
    fetchObjects: (query) =>
        aki(StagesApi)
            .stagesAllList(withQuery(query, { ordering: "name" }))
            .then(({ results }) => results),
    keyOf: (stage) => stage.pk,
    labelOf: (stage) => stage.name,
    groupBy: (stages) => groupBy(stages, (stage) => stage.verboseNamePlural),
};

function createInvalidResponseOptions(): RadioOption<InvalidResponseActionEnum>[] {
    return [
        {
            label: "RETRY",
            value: InvalidResponseActionEnum.Retry,
            default: true,
            description: msg("Returns the error message and a similar challenge to the executor"),
        },
        {
            label: "RESTART",
            value: InvalidResponseActionEnum.Restart,
            description: msg("Restarts the flow from the beginning"),
        },
        {
            label: "RESTART_WITH_CONTEXT",
            value: InvalidResponseActionEnum.RestartWithContext,
            description: msg(
                "Restarts the flow from the beginning, while keeping the flow context",
            ),
        },
    ];
}

@customElement("ak-stage-binding-form")
export class StageBindingForm extends ModelForm<FlowStageBinding, string> {
    public static override verboseName = msg("Stage Binding");
    public static override verboseNamePlural = msg("Stage Bindings");

    async load() {
        this.defaultOrder = await this.getOrder();
    }

    async loadInstance(pk: string): Promise<FlowStageBinding> {
        const binding = await aki(FlowsApi).flowsBindingsRetrieve({
            fsbUuid: pk,
        });

        return binding;
    }

    @property()
    public targetPk?: string;

    @state()
    protected defaultOrder = 0;

    public override reset(): void {
        super.reset();

        this.defaultOrder = 0;
    }

    getSuccessMessage(): string {
        if (this.instance?.pk) {
            return msg("Successfully updated binding.");
        }

        return msg("Successfully created binding.");
    }

    send(data: FlowStageBinding): Promise<unknown> {
        if (this.instance?.pk) {
            return aki(FlowsApi).flowsBindingsPartialUpdate({
                fsbUuid: this.instance.pk,
                patchedFlowStageBindingRequest: data,
            });
        }

        if (this.targetPk) {
            data.target = this.targetPk;
        }

        return aki(FlowsApi).flowsBindingsCreate({
            flowStageBindingRequest: data,
        });
    }

    async getOrder(): Promise<number> {
        if (this.instance?.pk) {
            return this.instance.order;
        }

        const bindings = await aki(FlowsApi).flowsBindingsList({
            target: this.targetPk || "",
        });

        const orders = bindings.results.map((binding) => binding.order);

        if (orders.length < 1) {
            return 0;
        }

        return Math.max(...orders) + 1;
    }

    renderTarget(): SlottedTemplateResult {
        if (this.instance?.target || this.targetPk) {
            return nothing;
        }

        return html`<ak-form-element-horizontal label=${msg("Target")} required name="target">
            ${AKFlowSearch({ name: "target", flowType: FlowDesignationEnum.Authorization, value: this.instance?.target, required: true })}
        </ak-form-element-horizontal>`;
    }

    protected override renderForm(): SlottedTemplateResult {
        return html`${this.renderTarget()}
            <ak-form-element-horizontal required name="stage">
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        required: true,
                    },
                    msg("Stage"),
                )}
                ${AKSearchSelect({
                    name: "stage",
                    source: stageSource,
                    label: msg("Stage"),
                    placeholder: msg("Select a stage..."),
                    value: this.instance?.stage,
                    selectedObject: this.instance?.stageObj,
                    blankable: false,
                })}
            </ak-form-element-horizontal>
            <ak-form-element-horizontal required name="order">
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "stage-binding-order",
                        required: true,
                    },
                    msg("Order"),
                )}
                <input
                    id="stage-binding-order"
                    type="number"
                    value="${this.instance?.order ?? this.defaultOrder}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-switch-input
                name="evaluateOnPlan"
                label=${msg("Evaluate when flow is planned")}
                ?checked=${this.instance?.evaluateOnPlan ?? false}
                help=${msg("Evaluate policies during the Flow planning process.")}
            >
            </ak-switch-input>
            <ak-switch-input
                name="reEvaluatePolicies"
                label=${msg("Evaluate when stage is run")}
                ?checked=${this.instance?.reEvaluatePolicies ?? true}
                help=${msg("Evaluate policies before the Stage is presented to the user.")}
            >
            </ak-switch-input>
            <ak-form-element-horizontal
                label=${msg("Invalid response behavior")}
                required
                name="invalidResponseAction"
            >
                <ak-radio
                    .options=${createInvalidResponseOptions()}
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
                required
                name="policyEngineMode"
            >
                <ak-radio .options=${policyEngineModes} .value=${this.instance?.policyEngineMode}>
                </ak-radio>
            </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-binding-form": StageBindingForm;
    }
}

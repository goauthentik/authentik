import { FlowsApi, FlowStageBinding, PolicyEngineMode, Stage, StagesApi } from "authentik-api";
import { t } from "@lingui/macro";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../api/Config";
import { until } from "lit-html/directives/until";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../elements/forms/HorizontalFormElement";
import { first, groupBy } from "../../utils";
import { ModelForm } from "../../elements/forms/ModelForm";

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
        if (this.instance) {
            return t`Successfully updated binding.`;
        } else {
            return t`Successfully created binding.`;
        }
    }

    send = (data: FlowStageBinding): Promise<FlowStageBinding> => {
        if (this.instance) {
            return new FlowsApi(DEFAULT_CONFIG).flowsBindingsUpdate({
                fsbUuid: this.instance.pk || "",
                flowStageBindingRequest: data
            });
        } else {
            return new FlowsApi(DEFAULT_CONFIG).flowsBindingsCreate({
                flowStageBindingRequest: data
            });
        }
    };

    groupStages(stages: Stage[]): TemplateResult {
        return html`
            <option value="">---------</option>
            ${groupBy<Stage>(stages, (s => s.verboseName || "")).map(([group, stages]) => {
                return html`<optgroup label=${group}>
                    ${stages.map(stage => {
                        const selected = (this.instance?.stage === stage.pk);
                        return html`<option ?selected=${selected} value=${ifDefined(stage.pk)}>${stage.name}</option>`;
                    })}
                </optgroup>`;
            })}
        `;
    }

    getOrder(): Promise<number> {
        if (this.instance) {
            return Promise.resolve(this.instance.order);
        }
        return new FlowsApi(DEFAULT_CONFIG).flowsBindingsList({
            target: this.targetPk || "",
        }).then(bindings => {
            const orders = bindings.results.map(binding => binding.order);
            if (orders.length < 1) {
                return 0;
            }
            return Math.max(...orders) + 1;
        });
    }

    renderTarget(): TemplateResult {
        if (this.instance?.target || this.targetPk) {
            return html`
            <input required name="target" type="hidden" value=${ifDefined(this.instance?.target || this.targetPk)}>
            `;
        }
        return html`<ak-form-element-horizontal
            label=${t`Target`}
            ?required=${true}
            name="target">
            <select class="pf-c-form-control">
                ${until(new FlowsApi(DEFAULT_CONFIG).flowsInstancesList({
                    ordering: "pk"
                }).then(flows => {
                    return flows.results.map(flow => {
                        // No ?selected check here, as this input isnt shown on update forms
                        return html`<option value=${ifDefined(flow.pk)}>${flow.name} (${flow.slug})</option>`;
                    });
                }), html`<option>${t`Loading...`}</option>`)}
            </select>
        </ak-form-element-horizontal>`;
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            ${this.renderTarget()}
            <ak-form-element-horizontal
                label=${t`Stage`}
                ?required=${true}
                name="stage">
                <select class="pf-c-form-control">
                    ${until(new StagesApi(DEFAULT_CONFIG).stagesAllList({
                        ordering: "pk"
                    }).then(stages => {
                        return this.groupStages(stages.results);
                    }), html`<option>${t`Loading...`}</option>`)}
                </select>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Order`}
                ?required=${true}
                name="order">
                <input type="number" value="${until(this.getOrder())}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="evaluateOnPlan">
                <div class="pf-c-check">
                    <input type="checkbox" class="pf-c-check__input" ?checked=${first(this.instance?.evaluateOnPlan, true)}>
                    <label class="pf-c-check__label">
                        ${t`Evaluate on plan`}
                    </label>
                </div>
                <p class="pf-c-form__helper-text">
                    ${t`Evaluate policies during the Flow planning process. Disable this for input-based policies. Should be used in conjunction with 'Re-evaluate policies', as with this option disabled, policies are **not** evaluated.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="reEvaluatePolicies">
                <div class="pf-c-check">
                    <input type="checkbox" class="pf-c-check__input" ?checked=${first(this.instance?.reEvaluatePolicies, false)}>
                    <label class="pf-c-check__label">
                        ${t`Re-evaluate policies`}
                    </label>
                </div>
                <p class="pf-c-form__helper-text">${t`Evaluate policies before the Stage is present to the user.`}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Policy engine mode`}
                ?required=${true}
                name="policyEngineMode">
                <select class="pf-c-form-control">
                    <option value=${PolicyEngineMode.Any} ?selected=${this.instance?.policyEngineMode === PolicyEngineMode.Any}>
                        ${t`ANY, any policy must match to include this stage access.`}
                    </option>
                    <option value=${PolicyEngineMode.All} ?selected=${this.instance?.policyEngineMode === PolicyEngineMode.All}>
                        ${t`ALL, all policies must match to include this stage access.`}
                    </option>
                </select>
            </ak-form-element-horizontal>
        </form>`;
    }

}

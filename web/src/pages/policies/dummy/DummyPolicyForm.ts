import { DummyPolicy, PoliciesApi } from "authentik-api";
import { t } from "@lingui/macro";
import { customElement } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../../elements/forms/HorizontalFormElement";
import "../../../elements/forms/FormGroup";
import { first } from "../../../utils";
import { ModelForm } from "../../../elements/forms/ModelForm";

@customElement("ak-policy-dummy-form")
export class DummyPolicyForm extends ModelForm<DummyPolicy, string> {

    loadInstance(pk: string): Promise<DummyPolicy> {
        return new PoliciesApi(DEFAULT_CONFIG).policiesDummyRetrieve({
            policyUuid: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated policy.`;
        } else {
            return t`Successfully created policy.`;
        }
    }

    send = (data: DummyPolicy): Promise<DummyPolicy> => {
        if (this.instance) {
            return new PoliciesApi(DEFAULT_CONFIG).policiesDummyUpdate({
                policyUuid: this.instance.pk || "",
                data: data
            });
        } else {
            return new PoliciesApi(DEFAULT_CONFIG).policiesDummyCreate({
                data: data
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <div class="form-help-text">
                ${t`A policy used for testing. Always returns the same result as specified below after waiting a random duration.`}
            </div>
            <ak-form-element-horizontal
                label=${t`Name`}
                ?required=${true}
                name="name">
                <input type="text" value="${ifDefined(this.instance?.name || "")}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="executionLogging">
                <div class="pf-c-check">
                    <input type="checkbox" class="pf-c-check__input" ?checked=${first(this.instance?.executionLogging, false)}>
                    <label class="pf-c-check__label">
                        ${t`Execution logging`}
                    </label>
                </div>
                <p class="pf-c-form__helper-text">
                    ${t`When this option is enabled, all executions of this policy will be logged. By default, only execution errors are logged.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header">
                    ${t`Policy-specific settings`}
                </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal name="result">
                        <div class="pf-c-check">
                            <input type="checkbox" class="pf-c-check__input" ?checked=${first(this.instance?.result, false)}>
                            <label class="pf-c-check__label">
                                ${t`Pass policy?`}
                            </label>
                        </div>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Wait (min)`}
                        ?required=${true}
                        name="waitMin">
                        <input type="number" value="${first(this.instance?.waitMin, 1)}" class="pf-c-form-control" required>
                        <p class="pf-c-form__helper-text">${t`The policy takes a random time to execute. This controls the minimum time it will take.`}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Wait (max)`}
                        ?required=${true}
                        name="waitMax">
                        <input type="number" value="${first(this.instance?.waitMax, 5)}" class="pf-c-form-control" required>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }

}

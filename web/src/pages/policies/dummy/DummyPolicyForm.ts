import { DummyPolicy, PoliciesApi } from "authentik-api";
import { t } from "@lingui/macro";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { Form } from "../../../elements/forms/Form";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../../elements/forms/HorizontalFormElement";
import "../../../elements/forms/FormGroup";
import { first } from "../../../utils";

@customElement("ak-policy-dummy-form")
export class DummyPolicyForm extends Form<DummyPolicy> {

    set policyUUID(value: string) {
        new PoliciesApi(DEFAULT_CONFIG).policiesDummyRead({
            policyUuid: value,
        }).then(policy => {
            this.policy = policy;
        });
    }

    @property({attribute: false})
    policy?: DummyPolicy;

    getSuccessMessage(): string {
        if (this.policy) {
            return t`Successfully updated policy.`;
        } else {
            return t`Successfully created policy.`;
        }
    }

    send = (data: DummyPolicy): Promise<DummyPolicy> => {
        if (this.policy) {
            return new PoliciesApi(DEFAULT_CONFIG).policiesDummyUpdate({
                policyUuid: this.policy.pk || "",
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
            <ak-form-element-horizontal
                label=${t`Name`}
                ?required=${true}
                name="name">
                <input type="text" value="${ifDefined(this.policy?.name || "")}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="executionLogging">
                <div class="pf-c-check">
                    <input type="checkbox" class="pf-c-check__input" ?checked=${this.policy?.executionLogging || false}>
                    <label class="pf-c-check__label">
                        ${t`Execution logging`}
                    </label>
                </div>
                <p class="pf-c-form__helper-text">${t`When this option is enabled, all executions of this policy will be logged. By default, only execution errors are logged.`}</p>
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header">
                    ${t`Policy-specific settings`}
                </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal name="result">
                        <div class="pf-c-check">
                            <input type="checkbox" class="pf-c-check__input" ?checked=${this.policy?.result || false}>
                            <label class="pf-c-check__label">
                                ${t`Pass policy?`}
                            </label>
                        </div>
                        <p class="pf-c-form__helper-text">${t`When this option is enabled, all executions of this policy will be logged. By default, only execution errors are logged.`}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Wait (min)`}
                        ?required=${true}
                        name="waitMin">
                        <input type="number" value="${first(this.policy?.waitMin, 1)}" class="pf-c-form-control" required>
                        <p class="pf-c-form__helper-text">${t`The policy takes a random time to execute. This controls the minimum time it will take.`}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Wait (max)`}
                        ?required=${true}
                        name="waitMax">
                        <input type="number" value="${first(this.policy?.waitMax, 5)}" class="pf-c-form-control" required>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }

}

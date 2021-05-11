import { ReputationPolicy, PoliciesApi } from "authentik-api";
import { t } from "@lingui/macro";
import { customElement } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../../elements/forms/HorizontalFormElement";
import "../../../elements/forms/FormGroup";
import { first } from "../../../utils";
import { ModelForm } from "../../../elements/forms/ModelForm";

@customElement("ak-policy-reputation-form")
export class ReputationPolicyForm extends ModelForm<ReputationPolicy, string> {

    loadInstance(pk: string): Promise<ReputationPolicy> {
        return new PoliciesApi(DEFAULT_CONFIG).policiesReputationRead({
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

    send = (data: ReputationPolicy): Promise<ReputationPolicy> => {
        if (this.instance) {
            return new PoliciesApi(DEFAULT_CONFIG).policiesReputationUpdate({
                policyUuid: this.instance.pk || "",
                data: data
            });
        } else {
            return new PoliciesApi(DEFAULT_CONFIG).policiesReputationCreate({
                data: data
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <div class="form-help-text">
                ${t`Allows/denys requests based on the users and/or the IPs reputation.`}
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
                    <ak-form-element-horizontal name="checkIp">
                        <div class="pf-c-check">
                            <input type="checkbox" class="pf-c-check__input" ?checked=${first(this.instance?.checkIp, false)}>
                            <label class="pf-c-check__label">
                                ${t`Check IP`}
                            </label>
                        </div>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="checkUsername">
                        <div class="pf-c-check">
                            <input type="checkbox" class="pf-c-check__input" ?checked=${first(this.instance?.checkUsername, false)}>
                            <label class="pf-c-check__label">
                                ${t`Check Username`}
                            </label>
                        </div>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Threshold`}
                        ?required=${true}
                        name="threshold">
                        <input type="number" value="${ifDefined(this.instance?.threshold || -5)}" class="pf-c-form-control" required>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }

}

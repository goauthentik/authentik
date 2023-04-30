import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { PoliciesApi, ReputationPolicy } from "@goauthentik/api";

@customElement("ak-policy-reputation-form")
export class ReputationPolicyForm extends ModelForm<ReputationPolicy, string> {
    loadInstance(pk: string): Promise<ReputationPolicy> {
        return new PoliciesApi(DEFAULT_CONFIG).policiesReputationRetrieve({
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

    async send(data: ReputationPolicy): Promise<ReputationPolicy> {
        if (this.instance) {
            return new PoliciesApi(DEFAULT_CONFIG).policiesReputationUpdate({
                policyUuid: this.instance.pk || "",
                reputationPolicyRequest: data,
            });
        } else {
            return new PoliciesApi(DEFAULT_CONFIG).policiesReputationCreate({
                reputationPolicyRequest: data,
            });
        }
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <div class="form-help-text">
                ${t`Allows/denys requests based on the users and/or the IPs reputation.`}
            </div>
            <div class="form-help-text">
                ${t`Invalid login attempts will decrease the score for the client's IP, and the
                username they are attempting to login as, by one.`}
            </div>
            <div class="form-help-text">
                ${t`The policy passes when the reputation score is below the threshold, and
                doesn't pass when either or both of the selected options are equal or above the
                threshold.`}
            </div>
            <ak-form-element-horizontal label=${t`Name`} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name || "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="executionLogging">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${first(this.instance?.executionLogging, false)}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${t`Execution logging`}</span>
                </label>
                <p class="pf-c-form__helper-text">
                    ${t`When this option is enabled, all executions of this policy will be logged. By default, only execution errors are logged.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header"> ${t`Policy-specific settings`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal name="checkIp">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${first(this.instance?.checkIp, false)}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label">${t`Check IP`}</span>
                        </label>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="checkUsername">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${first(this.instance?.checkUsername, false)}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label">${t`Check Username`}</span>
                        </label>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Threshold`}
                        ?required=${true}
                        name="threshold"
                    >
                        <input
                            type="number"
                            value="${ifDefined(this.instance?.threshold || -5)}"
                            class="pf-c-form-control"
                            required
                        />
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}

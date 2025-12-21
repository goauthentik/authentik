import "#components/ak-switch-input";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";

import { DEFAULT_CONFIG } from "#common/api/config";

import { BasePolicyForm } from "#admin/policies/BasePolicyForm";

import { PasswordExpiryPolicy, PoliciesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-policy-password-expiry-form")
export class PasswordExpiryPolicyForm extends BasePolicyForm<PasswordExpiryPolicy> {
    loadInstance(pk: string): Promise<PasswordExpiryPolicy> {
        return new PoliciesApi(DEFAULT_CONFIG).policiesPasswordExpiryRetrieve({
            policyUuid: pk,
        });
    }

    async send(data: PasswordExpiryPolicy): Promise<PasswordExpiryPolicy> {
        if (this.instance) {
            return new PoliciesApi(DEFAULT_CONFIG).policiesPasswordExpiryUpdate({
                policyUuid: this.instance.pk || "",
                passwordExpiryPolicyRequest: data,
            });
        }
        return new PoliciesApi(DEFAULT_CONFIG).policiesPasswordExpiryCreate({
            passwordExpiryPolicyRequest: data,
        });
    }

    renderForm(): TemplateResult {
        return html` <span>
                ${msg(
                    "Checks if the request's user's password has been changed in the last x days, and denys based on settings.",
                )}
            </span>
            <ak-form-element-horizontal label=${msg("Name")} required name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name || "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-switch-input
                name="executionLogging"
                label=${msg("Execution logging")}
                ?checked=${this.instance?.executionLogging ?? false}
                help=${msg(
                    "When this option is enabled, all executions of this policy will be logged. By default, only execution errors are logged.",
                )}
            >
            </ak-switch-input>
            <ak-form-group open label="${msg("Policy-specific settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Maximum age (in days)")}
                        required
                        name="days"
                    >
                        <input
                            type="number"
                            value="${ifDefined(this.instance?.days || "")}"
                            class="pf-c-form-control"
                            required
                        />
                    </ak-form-element-horizontal>
                    <ak-switch-input
                        name="denyOnly"
                        label=${msg("Only fail the policy, don't invalidate user's password")}
                        ?checked=${this.instance?.denyOnly ?? false}
                    >
                    </ak-switch-input>
                </div>
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-policy-password-expiry-form": PasswordExpiryPolicyForm;
    }
}

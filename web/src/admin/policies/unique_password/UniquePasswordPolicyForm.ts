import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";

import { DEFAULT_CONFIG } from "#common/api/config";

import { BasePolicyForm } from "#admin/policies/BasePolicyForm";

import { PoliciesApi, UniquePasswordPolicy } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-policy-password-uniqueness-form")
export class UniquePasswordPolicyForm extends BasePolicyForm<UniquePasswordPolicy> {
    async loadInstance(pk: string): Promise<UniquePasswordPolicy> {
        return new PoliciesApi(DEFAULT_CONFIG).policiesUniquePasswordRetrieve({
            policyUuid: pk,
        });
    }

    async send(data: UniquePasswordPolicy): Promise<UniquePasswordPolicy> {
        if (this.instance) {
            return new PoliciesApi(DEFAULT_CONFIG).policiesUniquePasswordUpdate({
                policyUuid: this.instance.pk || "",
                uniquePasswordPolicyRequest: data,
            });
        }
        return new PoliciesApi(DEFAULT_CONFIG).policiesUniquePasswordCreate({
            uniquePasswordPolicyRequest: data,
        });
    }

    renderForm(): TemplateResult {
        return html` <span>
                ${msg(
                    "Ensure that the user's new password is different from their previous passwords. The number of past passwords to check is configurable.",
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
            <ak-form-element-horizontal name="executionLogging">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${this.instance?.executionLogging ?? false}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${msg("Execution logging")}</span>
                </label>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "When this option is enabled, all executions of this policy will be logged. By default, only execution errors are logged.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Password field")}
                required
                name="passwordField"
            >
                <input
                    type="text"
                    value="${ifDefined(this.instance?.passwordField || "password")}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${msg("Field key to check, field keys defined in Prompt stages are available.")}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Number of previous passwords to check")}
                required
                name="numHistoricalPasswords"
            >
                <input
                    type="number"
                    value="${this.instance?.numHistoricalPasswords ?? 1}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-policy-password-uniqueness-form": UniquePasswordPolicyForm;
    }
}

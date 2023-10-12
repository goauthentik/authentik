import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { PasswordExpiryPolicy, PoliciesApi } from "@goauthentik/api";

@customElement("ak-policy-password-expiry-form")
export class PasswordExpiryPolicyForm extends ModelForm<PasswordExpiryPolicy, string> {
    loadInstance(pk: string): Promise<PasswordExpiryPolicy> {
        return new PoliciesApi(DEFAULT_CONFIG).policiesPasswordExpiryRetrieve({
            policyUuid: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("Successfully updated policy.");
        } else {
            return msg("Successfully created policy.");
        }
    }

    async send(data: PasswordExpiryPolicy): Promise<PasswordExpiryPolicy> {
        if (this.instance) {
            return new PoliciesApi(DEFAULT_CONFIG).policiesPasswordExpiryUpdate({
                policyUuid: this.instance.pk || "",
                passwordExpiryPolicyRequest: data,
            });
        } else {
            return new PoliciesApi(DEFAULT_CONFIG).policiesPasswordExpiryCreate({
                passwordExpiryPolicyRequest: data,
            });
        }
    }

    renderForm(): TemplateResult {
        return html` <span>
                ${msg(
                    "Checks if the request's user's password has been changed in the last x days, and denys based on settings.",
                )}
            </span>
            <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
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
                    <span class="pf-c-switch__label">${msg("Execution logging")}</span>
                </label>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "When this option is enabled, all executions of this policy will be logged. By default, only execution errors are logged.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header"> ${msg("Policy-specific settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Maximum age (in days)")}
                        ?required=${true}
                        name="days"
                    >
                        <input
                            type="number"
                            value="${ifDefined(this.instance?.days || "")}"
                            class="pf-c-form-control"
                            required
                        />
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="denyOnly">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${first(this.instance?.denyOnly, false)}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label"
                                >${msg(
                                    "Only fail the policy, don't invalidate user's password",
                                )}</span
                            >
                        </label>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>`;
    }
}

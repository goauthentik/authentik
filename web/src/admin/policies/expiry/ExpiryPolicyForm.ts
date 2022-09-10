import { DEFAULT_CONFIG } from "@goauthentik/web/api/Config";
import "@goauthentik/web/elements/forms/FormGroup";
import "@goauthentik/web/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/web/elements/forms/ModelForm";
import { first } from "@goauthentik/web/utils";

import { t } from "@lingui/macro";

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
            return t`Successfully updated policy.`;
        } else {
            return t`Successfully created policy.`;
        }
    }

    send = (data: PasswordExpiryPolicy): Promise<PasswordExpiryPolicy> => {
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
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <div class="form-help-text">
                ${t`Checks if the request's user's password has been changed in the last x days, and denys based on settings.`}
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
                <div class="pf-c-check">
                    <input
                        type="checkbox"
                        class="pf-c-check__input"
                        ?checked=${first(this.instance?.executionLogging, false)}
                    />
                    <label class="pf-c-check__label"> ${t`Execution logging`} </label>
                </div>
                <p class="pf-c-form__helper-text">
                    ${t`When this option is enabled, all executions of this policy will be logged. By default, only execution errors are logged.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header"> ${t`Policy-specific settings`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${t`Maximum age (in days)`}
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
                        <div class="pf-c-check">
                            <input
                                type="checkbox"
                                class="pf-c-check__input"
                                ?checked=${first(this.instance?.denyOnly, false)}
                            />
                            <label class="pf-c-check__label">
                                ${t`Only fail the policy, don't invalidate user's password.`}
                            </label>
                        </div>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}

import { DEFAULT_CONFIG } from "@goauthentik/web/api/Config";
import "@goauthentik/web/elements/forms/FormGroup";
import "@goauthentik/web/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/web/elements/forms/ModelForm";
import { first } from "@goauthentik/web/utils";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { HaveIBeenPwendPolicy, PoliciesApi } from "@goauthentik/api";

@customElement("ak-policy-hibp-form")
export class HaveIBeenPwnedPolicyForm extends ModelForm<HaveIBeenPwendPolicy, string> {
    loadInstance(pk: string): Promise<HaveIBeenPwendPolicy> {
        return new PoliciesApi(DEFAULT_CONFIG).policiesHaveibeenpwnedRetrieve({
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

    send = (data: HaveIBeenPwendPolicy): Promise<HaveIBeenPwendPolicy> => {
        if (this.instance) {
            return new PoliciesApi(DEFAULT_CONFIG).policiesHaveibeenpwnedUpdate({
                policyUuid: this.instance.pk || "",
                haveIBeenPwendPolicyRequest: data,
            });
        } else {
            return new PoliciesApi(DEFAULT_CONFIG).policiesHaveibeenpwnedCreate({
                haveIBeenPwendPolicyRequest: data,
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <div class="form-help-text">
                ${t`Checks a value from the policy request against the Have I been Pwned API, and denys the request based upon that.
                Note that only a part of the hash of the password is sent, the full comparison is done clientside.`}
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
                        label=${t`Password field`}
                        ?required=${true}
                        name="passwordField"
                    >
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.passwordField || "password")}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`Field key to check, field keys defined in Prompt stages are available.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Allowed count`}
                        ?required=${true}
                        name="allowedCount"
                    >
                        <input
                            type="number"
                            value="${first(this.instance?.allowedCount, 0)}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`Allow up to N occurrences in the HIBP database.`}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}

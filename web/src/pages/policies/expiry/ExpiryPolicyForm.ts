import { PasswordExpiryPolicy, PoliciesApi } from "authentik-api";
import { gettext } from "django";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { Form } from "../../../elements/forms/Form";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../../elements/forms/HorizontalFormElement";
import "../../../elements/forms/FormGroup";

@customElement("ak-policy-password-expiry-form")
export class PasswordExpiryPolicyForm extends Form<PasswordExpiryPolicy> {

    set policyUUID(value: string) {
        new PoliciesApi(DEFAULT_CONFIG).policiesPasswordExpiryRead({
            policyUuid: value,
        }).then(policy => {
            this.policy = policy;
        });
    }

    @property({attribute: false})
    policy?: PasswordExpiryPolicy;

    getSuccessMessage(): string {
        if (this.policy) {
            return gettext("Successfully updated policy.");
        } else {
            return gettext("Successfully created policy.");
        }
    }

    send = (data: PasswordExpiryPolicy): Promise<PasswordExpiryPolicy> => {
        if (this.policy) {
            return new PoliciesApi(DEFAULT_CONFIG).policiesPasswordExpiryUpdate({
                policyUuid: this.policy.pk || "",
                data: data
            });
        } else {
            return new PoliciesApi(DEFAULT_CONFIG).policiesPasswordExpiryCreate({
                data: data
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                label=${gettext("Name")}
                ?required=${true}
                name="name">
                <input type="text" value="${ifDefined(this.policy?.name || "")}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="executionLogging">
                <div class="pf-c-check">
                    <input type="checkbox" class="pf-c-check__input" ?checked=${this.policy?.executionLogging || false}>
                    <label class="pf-c-check__label">
                        ${gettext("Execution logging")}
                    </label>
                </div>
                <p class="pf-c-form__helper-text">${gettext("When this option is enabled, all executions of this policy will be logged. By default, only execution errors are logged.")}</p>
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header">
                    ${gettext("Policy-specific settings")}
                </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${gettext("Maximum age (in days)")}
                        ?required=${true}
                        name="days">
                        <input type="number" value="${ifDefined(this.policy?.days || "")}" class="pf-c-form-control" required>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="denyOnly">
                        <div class="pf-c-check">
                            <input type="checkbox" class="pf-c-check__input" ?checked=${this.policy?.denyOnly || false}>
                            <label class="pf-c-check__label">
                                ${gettext("Only fail the policy, don't set user's password.")}
                            </label>
                        </div>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }

}

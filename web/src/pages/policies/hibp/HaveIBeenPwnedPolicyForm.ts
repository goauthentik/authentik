import { HaveIBeenPwendPolicy, PoliciesApi } from "authentik-api";
import { gettext } from "django";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { Form } from "../../../elements/forms/Form";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../../elements/forms/HorizontalFormElement";
import "../../../elements/forms/FormGroup";

@customElement("ak-policy-hibp-form")
export class HaveIBeenPwnedPolicyForm extends Form<HaveIBeenPwendPolicy> {

    set policyUUID(value: string) {
        new PoliciesApi(DEFAULT_CONFIG).policiesHaveibeenpwnedRead({
            policyUuid: value,
        }).then(policy => {
            this.policy = policy;
        });
    }

    @property({attribute: false})
    policy?: HaveIBeenPwendPolicy;

    getSuccessMessage(): string {
        if (this.policy) {
            return gettext("Successfully updated policy.");
        } else {
            return gettext("Successfully created policy.");
        }
    }

    send = (data: HaveIBeenPwendPolicy): Promise<HaveIBeenPwendPolicy> => {
        if (this.policy) {
            return new PoliciesApi(DEFAULT_CONFIG).policiesHaveibeenpwnedUpdate({
                policyUuid: this.policy.pk || "",
                data: data
            });
        } else {
            return new PoliciesApi(DEFAULT_CONFIG).policiesHaveibeenpwnedCreate({
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
                        label=${gettext("Password field")}
                        ?required=${true}
                        name="passwordField">
                        <input type="text" value="${ifDefined(this.policy?.passwordField || "password")}" class="pf-c-form-control" required>
                        <p class="pf-c-form__helper-text">${gettext("Field key to check, field keys defined in Prompt stages are available.")}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${gettext("Allowed count")}
                        ?required=${true}
                        name="allowedCount">
                        <input type="number" value="${ifDefined(this.policy?.allowedCount || 0)}" class="pf-c-form-control" required>
                        <p class="pf-c-form__helper-text">${gettext("Allow up to N occurrences in the HIBP database.")}</p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }

}

import { PasswordPolicy, PoliciesApi } from "authentik-api";
import { gettext } from "django";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { Form } from "../../../elements/forms/Form";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../../elements/forms/HorizontalFormElement";
import "../../../elements/forms/FormGroup";
import { first } from "../../../utils";

@customElement("ak-policy-password-form")
export class PasswordPolicyForm extends Form<PasswordPolicy> {

    set policyUUID(value: string) {
        new PoliciesApi(DEFAULT_CONFIG).policiesPasswordRead({
            policyUuid: value,
        }).then(policy => {
            this.policy = policy;
        });
    }

    @property({attribute: false})
    policy?: PasswordPolicy;

    getSuccessMessage(): string {
        if (this.policy) {
            return gettext("Successfully updated policy.");
        } else {
            return gettext("Successfully created policy.");
        }
    }

    send = (data: PasswordPolicy): Promise<PasswordPolicy> => {
        if (this.policy) {
            return new PoliciesApi(DEFAULT_CONFIG).policiesPasswordUpdate({
                policyUuid: this.policy.pk || "",
                data: data
            });
        } else {
            return new PoliciesApi(DEFAULT_CONFIG).policiesPasswordCreate({
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
                        label=${gettext("Minimum length")}
                        ?required=${true}
                        name="lengthMin">
                        <input type="number" value="${first(this.policy?.lengthMin, 10)}" class="pf-c-form-control" required>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${gettext("Minimum amount of Uppercase Characters")}
                        ?required=${true}
                        name="amountUppercase">
                        <input type="number" value="${first(this.policy?.amountUppercase, 2)}" class="pf-c-form-control" required>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${gettext("Minimum amount of Lowercase Characters")}
                        ?required=${true}
                        name="amountLowercase">
                        <input type="number" value="${first(this.policy?.amountLowercase, 2)}" class="pf-c-form-control" required>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${gettext("Minimum amount of Symbols Characters")}
                        ?required=${true}
                        name="amountSymbols">
                        <input type="number" value="${first(this.policy?.amountSymbols, 2)}" class="pf-c-form-control" required>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${gettext("Error message")}
                        ?required=${true}
                        name="errorMessage">
                        <input type="text" value="${ifDefined(this.policy?.errorMessage)}" class="pf-c-form-control" required>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group>
                <span slot="header">
                    ${gettext("Advanced settings")}
                </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${gettext("Symbol charset")}
                        ?required=${true}
                        name="symbolCharset">
                        <input type="text" value="${ifDefined(this.policy?.symbolCharset || "!\\\"#$%&'()*+,-./:;<=>?@[]^_`{|}~ ")}" class="pf-c-form-control" required>
                        <p class="pf-c-form__helper-text">${gettext("Characters which are considered as symbols.")}</p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }

}

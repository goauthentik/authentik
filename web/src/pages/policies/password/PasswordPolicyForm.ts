import { PasswordPolicy, PoliciesApi } from "@goauthentik/api";
import { t } from "@lingui/macro";
import { customElement } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../../elements/forms/HorizontalFormElement";
import "../../../elements/forms/FormGroup";
import { first } from "../../../utils";
import { ModelForm } from "../../../elements/forms/ModelForm";

@customElement("ak-policy-password-form")
export class PasswordPolicyForm extends ModelForm<PasswordPolicy, string> {
    loadInstance(pk: string): Promise<PasswordPolicy> {
        return new PoliciesApi(DEFAULT_CONFIG).policiesPasswordRetrieve({
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

    send = (data: PasswordPolicy): Promise<PasswordPolicy> => {
        if (this.instance) {
            return new PoliciesApi(DEFAULT_CONFIG).policiesPasswordUpdate({
                policyUuid: this.instance.pk || "",
                passwordPolicyRequest: data,
            });
        } else {
            return new PoliciesApi(DEFAULT_CONFIG).policiesPasswordCreate({
                passwordPolicyRequest: data,
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <div class="form-help-text">
                ${t`Checks the value from the policy request against several rules, mostly used to ensure password strength.`}
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
                        label=${t`Minimum length`}
                        ?required=${true}
                        name="lengthMin"
                    >
                        <input
                            type="number"
                            value="${first(this.instance?.lengthMin, 10)}"
                            class="pf-c-form-control"
                            required
                        />
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Minimum amount of Uppercase Characters`}
                        ?required=${true}
                        name="amountUppercase"
                    >
                        <input
                            type="number"
                            value="${first(this.instance?.amountUppercase, 2)}"
                            class="pf-c-form-control"
                            required
                        />
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Minimum amount of Lowercase Characters`}
                        ?required=${true}
                        name="amountLowercase"
                    >
                        <input
                            type="number"
                            value="${first(this.instance?.amountLowercase, 2)}"
                            class="pf-c-form-control"
                            required
                        />
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Minimum amount of Symbols Characters`}
                        ?required=${true}
                        name="amountSymbols"
                    >
                        <input
                            type="number"
                            value="${first(this.instance?.amountSymbols, 2)}"
                            class="pf-c-form-control"
                            required
                        />
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Error message`}
                        ?required=${true}
                        name="errorMessage"
                    >
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.errorMessage)}"
                            class="pf-c-form-control"
                            required
                        />
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group>
                <span slot="header"> ${t`Advanced settings`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${t`Symbol charset`}
                        ?required=${true}
                        name="symbolCharset"
                    >
                        <input
                            type="text"
                            value="${ifDefined(
                                this.instance?.symbolCharset ||
                                    "!\\\"#$%&'()*+,-./:;<=>?@[]^_`{|}~ ",
                            )}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`Characters which are considered as symbols.`}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}

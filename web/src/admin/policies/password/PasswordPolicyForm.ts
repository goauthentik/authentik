import { BasePolicyForm } from "@goauthentik/admin/policies/BasePolicyForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { PasswordPolicy, PoliciesApi } from "@goauthentik/api";

@customElement("ak-policy-password-form")
export class PasswordPolicyForm extends BasePolicyForm<PasswordPolicy> {
    @state()
    showStatic = true;

    @state()
    showHIBP = false;

    @state()
    showZxcvbn = false;

    async loadInstance(pk: string): Promise<PasswordPolicy> {
        const policy = await new PoliciesApi(DEFAULT_CONFIG).policiesPasswordRetrieve({
            policyUuid: pk,
        });
        this.showStatic = policy.checkStaticRules || false;
        this.showHIBP = policy.checkHaveIBeenPwned || false;
        this.showZxcvbn = policy.checkZxcvbn || false;
        return policy;
    }

    async send(data: PasswordPolicy): Promise<PasswordPolicy> {
        if (this.instance) {
            return new PoliciesApi(DEFAULT_CONFIG).policiesPasswordUpdate({
                policyUuid: this.instance.pk || "",
                passwordPolicyRequest: data,
            });
        }
        return new PoliciesApi(DEFAULT_CONFIG).policiesPasswordCreate({
            passwordPolicyRequest: data,
        });
    }

    renderStaticRules(): TemplateResult {
        return html` <ak-form-group label="${msg("Static rules")}">
            <div class="pf-c-form">
                <ak-form-element-horizontal
                    label=${msg("Minimum length")}
                    required
                    name="lengthMin"
                >
                    <input
                        type="number"
                        value="${this.instance?.lengthMin ?? 10}"
                        class="pf-c-form-control"
                        required
                    />
                </ak-form-element-horizontal>
                <ak-form-element-horizontal
                    label=${msg("Minimum amount of Uppercase Characters")}
                    required
                    name="amountUppercase"
                >
                    <input
                        type="number"
                        value="${this.instance?.amountUppercase ?? 2}"
                        class="pf-c-form-control"
                        required
                    />
                </ak-form-element-horizontal>
                <ak-form-element-horizontal
                    label=${msg("Minimum amount of Lowercase Characters")}
                    required
                    name="amountLowercase"
                >
                    <input
                        type="number"
                        value="${this.instance?.amountLowercase ?? 2}"
                        class="pf-c-form-control"
                        required
                    />
                </ak-form-element-horizontal>
                <ak-form-element-horizontal
                    label=${msg("Minimum amount of Digits")}
                    required
                    name="amountDigits"
                >
                    <input
                        type="number"
                        value="${this.instance?.amountDigits ?? 2}"
                        class="pf-c-form-control"
                        required
                    />
                </ak-form-element-horizontal>
                <ak-form-element-horizontal
                    label=${msg("Minimum amount of Symbols Characters")}
                    required
                    name="amountSymbols"
                >
                    <input
                        type="number"
                        value="${this.instance?.amountSymbols ?? 2}"
                        class="pf-c-form-control"
                        required
                    />
                </ak-form-element-horizontal>
                <ak-form-element-horizontal
                    label=${msg("Error message")}
                    required
                    name="errorMessage"
                >
                    <input
                        type="text"
                        value="${ifDefined(this.instance?.errorMessage)}"
                        class="pf-c-form-control"
                        required
                    />
                </ak-form-element-horizontal>
                <ak-form-element-horizontal
                    label=${msg("Symbol charset")}
                    required
                    name="symbolCharset"
                >
                    <input
                        type="text"
                        value="${ifDefined(
                            this.instance?.symbolCharset || "!\\\"#$%&'()*+,-./:;<=>?@[]^_`{|}~ ",
                        )}"
                        class="pf-c-form-control"
                        required
                    />
                    <p class="pf-c-form__helper-text">
                        ${msg("Characters which are considered as symbols.")}
                    </p>
                </ak-form-element-horizontal>
            </div>
        </ak-form-group>`;
    }

    renderHIBP(): TemplateResult {
        return html`
            <ak-form-group open label="${msg("HaveIBeenPwned settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Allowed count")}
                        required
                        name="hibpAllowedCount"
                    >
                        <input
                            type="number"
                            value="${this.instance?.hibpAllowedCount ?? 0}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Allow up to N occurrences in the HIBP database.")}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        `;
    }

    renderZxcvbn(): TemplateResult {
        return html`
            <ak-form-group open label="${msg("zxcvbn settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Score threshold")}
                        required
                        name="zxcvbnScoreThreshold"
                    >
                        <input
                            type="number"
                            value="${this.instance?.zxcvbnScoreThreshold ?? 0}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "If the password's score is less than or equal this value, the policy will fail.",
                            )}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${msg("0: Too guessable: risky password. (guesses &lt; 10^3)")}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "1: Very guessable: protection from throttled online attacks. (guesses &lt; 10^6)",
                            )}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "2: Somewhat guessable: protection from unthrottled online attacks. (guesses &lt; 10^8)",
                            )}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "3: Safely unguessable: moderate protection from offline slow-hash scenario. (guesses &lt; 10^10)",
                            )}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "4: Very unguessable: strong protection from offline slow-hash scenario. (guesses &gt;= 10^10)",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        `;
    }

    renderForm(): TemplateResult {
        return html` <span>
                ${msg(
                    "Checks the value from the policy request against several rules, mostly used to ensure password strength.",
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

            <ak-form-element-horizontal name="checkStaticRules">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${this.instance?.checkStaticRules ?? true}
                        @change=${(ev: Event) => {
                            const el = ev.target as HTMLInputElement;
                            this.showStatic = el.checked;
                        }}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${msg("Check static rules")}</span>
                </label>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="checkHaveIBeenPwned">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${this.instance?.checkHaveIBeenPwned ?? true}
                        @change=${(ev: Event) => {
                            const el = ev.target as HTMLInputElement;
                            this.showHIBP = el.checked;
                        }}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${msg("Check haveibeenpwned.com")}</span>
                </label>
                <p class="pf-c-form__helper-text">
                    ${msg("For more info see:")}
                    <a href="https://haveibeenpwned.com/API/v2#SearchingPwnedPasswordsByRange"
                        >haveibeenpwned.com</a
                    >
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="checkZxcvbn">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${this.instance?.checkZxcvbn ?? true}
                        @change=${(ev: Event) => {
                            const el = ev.target as HTMLInputElement;
                            this.showZxcvbn = el.checked;
                        }}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${msg("Check zxcvbn")}</span>
                </label>
                <p class="pf-c-form__helper-text">
                    ${msg("Password strength estimator created by Dropbox, see:")}
                    <a href="https://github.com/dropbox/zxcvbn#readme">dropbox/zxcvbn</a>
                </p>
            </ak-form-element-horizontal>
            ${this.showStatic ? this.renderStaticRules() : html``}
            ${this.showHIBP ? this.renderHIBP() : html``}
            ${this.showZxcvbn ? this.renderZxcvbn() : html``}`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-policy-password-form": PasswordPolicyForm;
    }
}

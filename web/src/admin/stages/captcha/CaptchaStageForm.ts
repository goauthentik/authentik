import { BaseStageForm } from "@goauthentik/admin/stages/BaseStageForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { globalAK } from "@goauthentik/common/global";
import "@goauthentik/components/ak-number-input";
import "@goauthentik/components/ak-switch-input";
import "@goauthentik/elements/buttons/ModalButton";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { CaptchaStage, CaptchaStageRequest, StagesApi } from "@goauthentik/api";

import { css } from "lit";

type CaptchaProvider = "recaptcha" | "hcaptcha" | "turnstile" | "custom";

interface ProviderConfig {
    jsUrl: string;
    apiUrl: string;
    name: string;
}

const PROVIDER_CONFIGS: Record<CaptchaProvider, ProviderConfig> = {
    recaptcha: {
        jsUrl: "https://www.recaptcha.net/recaptcha/api.js",
        apiUrl: "https://www.recaptcha.net/recaptcha/api/siteverify",
        name: "Google reCAPTCHA",
    },
    hcaptcha: {
        jsUrl: "https://js.hcaptcha.com/1/api.js",
        apiUrl: "https://hcaptcha.com/siteverify",
        name: "hCaptcha",
    },
    turnstile: {
        jsUrl: "https://challenges.cloudflare.com/turnstile/v0/api.js",
        apiUrl: "https://challenges.cloudflare.com/turnstile/v0/siteverify",
        name: "Cloudflare Turnstile",
    },
    custom: {
        jsUrl: "",
        apiUrl: "",
        name: "Custom Provider",
    },
};

@customElement("ak-stage-captcha-form")
export class CaptchaStageForm extends BaseStageForm<CaptchaStage> {
    @state()
    selectedProvider: CaptchaProvider = "recaptcha";

    @state()
    isCustomMode = false;

    @state()
    isConfigLoaded = false;

    constructor() {
        super();
        // Wait for globalAK to be initialized
        const checkConfig = () => {
            if (globalAK().config) {
                this.isConfigLoaded = true;
                this.requestUpdate();
            } else {
                setTimeout(checkConfig, 100);
            }
        };
        checkConfig();
    }

    loadInstance(pk: string): Promise<CaptchaStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesCaptchaRetrieve({
            stageUuid: pk,
        });
    }

    async send(data: CaptchaStage): Promise<CaptchaStage> {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesCaptchaPartialUpdate({
                stageUuid: this.instance.pk || "",
                patchedCaptchaStageRequest: data,
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesCaptchaCreate({
                captchaStageRequest: data as unknown as CaptchaStageRequest,
            });
        }
    }

    private handleProviderSelect(provider: CaptchaProvider) {
        // If switching provider and currently in custom mode (fields have been edited), reset both URLs
        if (this.isCustomMode) {
            this.selectedProvider = provider;
            this.isCustomMode = provider === "custom";
            const config = PROVIDER_CONFIGS[provider];
            const form = this.querySelector("form");
            if (form) {
                const jsUrlInput = form.querySelector('input[name="jsUrl"]') as HTMLInputElement;
                const apiUrlInput = form.querySelector('input[name="apiUrl"]') as HTMLInputElement;
                if (jsUrlInput) jsUrlInput.value = config.jsUrl;
                if (apiUrlInput) apiUrlInput.value = config.apiUrl;
            }
        } else {
            // Normal provider switch: update both fields
            this.selectedProvider = provider;
            this.isCustomMode = provider === "custom";
            const config = PROVIDER_CONFIGS[provider];
            const form = this.querySelector("form");
            if (form) {
                const jsUrlInput = form.querySelector('input[name="jsUrl"]') as HTMLInputElement;
                const apiUrlInput = form.querySelector('input[name="apiUrl"]') as HTMLInputElement;
                if (jsUrlInput) jsUrlInput.value = config.jsUrl;
                if (apiUrlInput) apiUrlInput.value = config.apiUrl;
            }
        }
    }

    private handleUrlChange(e: Event) {
        // Only switch to custom mode and update the field that was changed
        const input = e.target as HTMLInputElement;
        const form = this.querySelector("form");
        if (!this.isCustomMode) {
            this.isCustomMode = true;
            this.selectedProvider = "custom";
            // Do not overwrite the other field
        }
        // The changed value is already in the input, so nothing else to do
    }

    static get styles() {
        return [
            ...super.styles,
            css`
                .form-description {
                    display: block;
                    margin-bottom: 1rem;
                    font-size: 0.95rem;
                    line-height: 1.4;
                }
                ak-form-group {
                    margin-bottom: 0.75rem;
                    min-height: unset;
                    border-radius: 3px;
                    overflow: hidden;
                }
                ak-form-group::part(header) {
                    padding: 0.5rem 0.75rem;
                    font-size: 0.875rem;
                    font-weight: 500;
                    background-color: var(--pf-global--BackgroundColor--200);
                    border: none;
                }
                ak-form-group::part(body) {
                    padding: 0.5rem 0.75rem;
                    background-color: var(--pf-global--BackgroundColor--100);
                }
                ak-form-element-horizontal {
                    margin-bottom: 0.75rem;
                    --ak-form-element-label-font-size: 0.875rem;
                }
                ak-form-element-horizontal:last-child {
                    margin-bottom: 0;
                }
                ak-form-element-horizontal::part(label) {
                    padding-top: 0.375rem;
                    margin-bottom: 0.5rem;
                }
                .form-row {
                    display: flex;
                    margin-bottom: 0.75rem;
                }
                .form-row ak-form-group {
                    flex: 1;
                    margin-bottom: 0;
                }
                .threshold-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 1rem;
                }
                .options-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 1rem;
                }
                .pf-c-form-group-body {
                    padding: 0;
                }
                input, select {
                    padding: 0.375rem 0.75rem;
                    min-height: 2rem;
                    font-size: 0.875rem;
                    line-height: 1.5;
                }
                input[type="url"], input[type="text"] {
                    height: 2.25rem;
                    box-sizing: border-box;
                }
                .pf-c-form-control {
                    width: 100%;
                }
                .pf-c-form__helper-text {
                    margin-top: 0.25rem;
                    font-size: 0.75rem;
                    line-height: 1.3;
                    color: var(--pf-global--Color--200);
                }
                ak-number-input {
                    margin-bottom: 0.75rem;
                    display: block;
                    --ak-number-input-label-font-size: 0.875rem;
                }
                ak-number-input:last-child {
                    margin-bottom: 0;
                }
                .threshold-grid ak-number-input {
                    margin-bottom: 0;
                }
                ak-switch-input {
                    margin-bottom: 0.75rem;
                    display: block;
                    --ak-switch-input-label-font-size: 0.875rem;
                }
                ak-switch-input:last-child {
                    margin-bottom: 0;
                }
                .options-grid ak-switch-input {
                    margin-bottom: 0;
                }
                .pf-c-switch {
                    display: flex;
                    align-items: center;
                }
                .pf-c-switch__label {
                    font-size: 0.875rem;
                    margin-left: 0.75rem;
                }
                .switch-container {
                    margin-bottom: 0.75rem;
                }
                .switch-helper-text {
                    margin-left: 2.5rem;
                    margin-top: 0.25rem;
                    font-size: 0.75rem;
                    color: var(--pf-global--Color--200);
                }
            `
        ];
    }

    renderForm(): TemplateResult {
        if (!this.isConfigLoaded) {
            return html`<ak-empty-state loading></ak-empty-state>`;
        }

        return html`
            <span class="form-description">
                ${msg("This stage verifies user interactions using a CAPTCHA service.")}
            </span>

            <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name || "")}" 
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            
            <ak-form-group .expanded=${true}>
                <span slot="header">${msg("Provider Settings")}</span>
                <div slot="body" class="pf-c-form-group-body">
                    <ak-form-element-horizontal label=${msg("Provider")} ?required=${true} name="provider">
                        <select
                            class="pf-c-form-control"
                            @change=${(e: Event) => this.handleProviderSelect((e.target as HTMLSelectElement).value as CaptchaProvider)}
                            .value=${this.selectedProvider}
                        >
                            <option value="recaptcha">${msg("Google reCAPTCHA")}</option>
                            <option value="hcaptcha">${msg("hCaptcha")}</option>
                            <option value="turnstile">${msg("Cloudflare Turnstile")}</option>
                            <option value="custom">${msg("Custom Provider")}</option>
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${msg("Select your CAPTCHA service provider")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("JS URL")} ?required=${true} name="jsUrl">
                        <input
                            type="url"
                            value="${ifDefined(
                                this.instance?.jsUrl ||
                                    PROVIDER_CONFIGS[this.selectedProvider].jsUrl,
                            )}"
                            class="pf-c-form-control pf-m-monospace"
                            autocomplete="off"
                            spellcheck="false"
                            required
                            @change=${this.handleUrlChange}
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("URL to fetch JavaScript from. This will be automatically set based on your provider selection.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("API URL")} ?required=${true} name="apiUrl">
                        <input
                            type="url"
                            value="${ifDefined(
                                this.instance?.apiUrl ||
                                    PROVIDER_CONFIGS[this.selectedProvider].apiUrl,
                            )}"
                            class="pf-c-form-control pf-m-monospace"
                            autocomplete="off"
                            spellcheck="false"
                            required
                            @change=${this.handleUrlChange}
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("URL to validate captcha response. This will be automatically set based on your provider selection.")}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>

            <div class="form-row">
                <ak-form-group .expanded=${true}>
                    <span slot="header">${msg("Keys")}</span>
                    <div slot="body" class="pf-c-form-group-body">
                        <ak-form-element-horizontal label=${msg("Public Key")} ?required=${true} name="publicKey">
                            <input
                                type="text"
                                value="${ifDefined(this.instance?.publicKey || "")}" 
                                class="pf-c-form-control pf-m-monospace"
                                autocomplete="off"
                                spellcheck="false"
                                required
                            />
                            <p class="pf-c-form__helper-text">
                                ${msg("CAPTCHA service public identifier")}
                            </p>
                        </ak-form-element-horizontal>
                        <ak-form-element-horizontal 
                            label=${msg("Private Key")} 
                            ?required=${true} 
                            ?writeOnly=${this.instance !== undefined}
                            name="privateKey"
                        >
                            <input
                                type="text"
                                value=""
                                class="pf-c-form-control pf-m-monospace"
                                autocomplete="off"
                                spellcheck="false"
                                required
                            />
                            <p class="pf-c-form__helper-text">
                                ${msg("CAPTCHA service secret key")}
                            </p>
                        </ak-form-element-horizontal>
                    </div>
                </ak-form-group>
            </div>

            <ak-form-group .expanded=${true}>
                <span slot="header">${msg("Score Thresholds")}</span>
                <div slot="body" class="pf-c-form-group-body">
                    <ak-number-input
                        label=${msg("Minimum Score Threshold")}
                        required
                        name="scoreMinThreshold"
                        value="${ifDefined(this.instance?.scoreMinThreshold || 0.5)}"
                        help=${msg("Minimum verification score (0.0-1.0)")}
                    ></ak-number-input>
                    <ak-number-input
                        label=${msg("Maximum Score Threshold")}
                        required
                        name="scoreMaxThreshold"
                        value="${ifDefined(this.instance?.scoreMaxThreshold || 1)}"
                        help=${msg("Maximum verification score (0.0-1.0)")}
                    ></ak-number-input>
                </div>
            </ak-form-group>

            <ak-form-group .expanded=${true}>
                <span slot="header">${msg("Options")}</span>
                <div slot="body" class="pf-c-form-group-body">
                    <ak-switch-input
                        name="interactive"
                        label=${msg("Interactive Mode")}
                        ?checked="${this.instance?.interactive}"
                        help=${msg("Requires direct user interaction with the CAPTCHA")}
                    >
                    </ak-switch-input>
                    <ak-switch-input
                        name="errorOnInvalidScore"
                        label=${msg("Enforce Score Validation")}
                        ?checked=${this.instance?.errorOnInvalidScore ?? true}
                        help=${msg("Block requests that fail score validation")}
                    >
                    </ak-switch-input>
                </div>
            </ak-form-group>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-captcha-form": CaptchaStageForm;
    }
}

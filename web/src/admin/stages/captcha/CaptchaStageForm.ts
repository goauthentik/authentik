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
                .section-label {
                    font-weight: 600;
                    margin-top: 2em;
                    margin-bottom: 0.5em;
                    color: var(--pf-global--Color--100, #fff);
                    font-size: 1.05em;
                    letter-spacing: 0.01em;
                }
                ak-form-group {
                    margin-bottom: 2.5rem;
                }
                ak-form-element-horizontal {
                    margin-bottom: 2rem;
                    padding-top: 0.5rem;
                    padding-bottom: 0.5rem;
                }
                .form-control-container {
                    width: 100%;
                }
                input, select {
                    padding: 0.75rem 1rem;
                    min-height: 3rem;
                }
                .pf-c-form__helper-text {
                    margin-top: 0.75rem;
                    font-size: 0.9rem;
                }
                .pf-c-switch {
                    margin-bottom: 0.75rem;
                    display: flex;
                    align-items: center;
                }
                .pf-c-switch__label {
                    font-size: 1rem;
                    margin-left: 1rem;
                }
                .switch-container {
                    margin-bottom: 1.5rem;
                }
                .switch-helper-text {
                    margin-left: 3.5rem;
                    margin-top: 0.5rem;
                    font-size: 0.9rem;
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
            <span>
                ${msg("This stage verifies user interactions using a CAPTCHA service.")}
            </span>

            <ak-form-group .expanded=${true}>
                <span slot="header">${msg("Provider Settings")}</span>
                <div slot="body">
                    <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.name || "")}" 
                            class="pf-c-form-control"
                            required
                        />
                    </ak-form-element-horizontal>
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
                            ${msg("URL used to validate captcha response. This will be automatically set based on your provider selection.")}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>

            <ak-form-group .expanded=${true}>
                <span slot="header">${msg("Keys")}</span>
                <div slot="body">
                    <ak-form-element-horizontal label=${msg("Public Key")} ?required=${true} name="publicKey">
                        <div class="form-control-container">
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
                        </div>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("Private Key")} ?required=${true} name="privateKey">
                        <div class="form-control-container">
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
                        </div>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>

            <ak-form-group .expanded=${true}>
                <span slot="header">${msg("Score Thresholds")}</span>
                <div slot="body">
                    <ak-form-element-horizontal label=${msg("Minimum Score Threshold")} name="scoreMinThreshold">
                        <div class="form-control-container">
                            <input
                                type="number"
                                min="0"
                                max="1"
                                step="0.01"
                                value="${ifDefined(this.instance?.scoreMinThreshold || 0.5)}"
                                class="pf-c-form-control"
                                required
                            />
                            <p class="pf-c-form__helper-text">
                                ${msg("Minimum verification score (0.0-1.0)")}
                            </p>
                        </div>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("Maximum Score Threshold")} name="scoreMaxThreshold">
                        <div class="form-control-container">
                            <input
                                type="number"
                                min="0"
                                max="1"
                                step="0.01"
                                value="${ifDefined(this.instance?.scoreMaxThreshold || 1)}"
                                class="pf-c-form-control"
                                required
                            />
                            <p class="pf-c-form__helper-text">
                                ${msg("Maximum verification score (0.0-1.0)")}
                            </p>
                        </div>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>

            <ak-form-group .expanded=${true}>
                <span slot="header">${msg("Options")}</span>
                <div slot="body">
                    <div class="switch-container">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                name="interactive"
                                ?checked=${this.instance?.interactive ?? false}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label">${msg("Interactive Mode")}</span>
                        </label>
                        <div class="switch-helper-text">
                            ${msg("Requires direct user interaction with the CAPTCHA")}
                        </div>
                    </div>
                    
                    <div class="switch-container">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                name="errorOnInvalidScore"
                                ?checked=${this.instance?.errorOnInvalidScore ?? true}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label">${msg("Enforce Score Validation")}</span>
                        </label>
                        <div class="switch-helper-text">
                            ${msg("Block requests that fail score validation")}
                        </div>
                    </div>
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

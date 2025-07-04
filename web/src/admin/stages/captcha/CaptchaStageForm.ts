import { BaseStageForm } from "@goauthentik/admin/stages/BaseStageForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { globalAK } from "@goauthentik/common/global";
import "@goauthentik/components/ak-number-input";
import "@goauthentik/components/ak-radio-input";
import "@goauthentik/components/ak-secret-text-input.js";
import "@goauthentik/components/ak-switch-input";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/EmptyState";
import "@goauthentik/elements/Expand";
import "@goauthentik/components/ak-hidden-text-input";

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
    helpUrl: string;
    description: string;
}

const PROVIDER_CONFIGS: Record<CaptchaProvider, ProviderConfig> = {
    recaptcha: {
        jsUrl: "https://www.recaptcha.net/recaptcha/api.js",
        apiUrl: "https://www.recaptcha.net/recaptcha/api/siteverify",
        name: "Google reCAPTCHA",
        helpUrl: "https://developers.google.com/recaptcha/docs/v3",
        description: msg("Google's bot detection service."),
    },
    hcaptcha: {
        jsUrl: "https://js.hcaptcha.com/1/api.js",
        apiUrl: "https://hcaptcha.com/siteverify",
        name: "hCaptcha",
        helpUrl: "https://docs.hcaptcha.com/",
        description: msg("Privacy-focused CAPTCHA alternative."),
    },
    turnstile: {
        jsUrl: "https://challenges.cloudflare.com/turnstile/v0/api.js",
        apiUrl: "https://challenges.cloudflare.com/turnstile/v0/siteverify",
        name: "Cloudflare Turnstile",
        helpUrl: "https://developers.cloudflare.com/turnstile/",
        description: msg("A user-friendly, privacy-preserving CAPTCHA replacement."),
    },
    custom: {
        jsUrl: "",
        apiUrl: "",
        name: "Custom Provider",
        helpUrl: "",
        description: msg("Configure a custom or self-hosted CAPTCHA service."),
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

    @state() advancedOpen = false;

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

    updated = (changedProps: Map<string, unknown>) => {
        super.updated?.(changedProps);
        if (changedProps.has('instance') && this.isConfigLoaded && this.instance) {
            // Set initial provider based on instance if available
            const jsUrl = this.instance.jsUrl || "";
            const jsUrlToProvider: Record<string, CaptchaProvider> = Object.fromEntries(
                Object.entries(PROVIDER_CONFIGS).map(([provider, config]) => [config.jsUrl, provider as CaptchaProvider])
            );
            const detected = jsUrlToProvider[jsUrl] || "custom";
            this.selectedProvider = detected;
            this.isCustomMode = detected === "custom";
        }
    }

    loadInstance(pk: string): Promise<CaptchaStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesCaptchaRetrieve({
            stageUuid: pk,
        });
    }

    async send(data: CaptchaStage): Promise<CaptchaStage> {
        // Ensure JS/API URLs match selected provider unless custom
        if (!this.isCustomMode) {
            data.jsUrl = PROVIDER_CONFIGS[this.selectedProvider].jsUrl;
            data.apiUrl = PROVIDER_CONFIGS[this.selectedProvider].apiUrl;
        }
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesCaptchaPartialUpdate({
                stageUuid: this.instance.pk || "",
                patchedCaptchaStageRequest: data,
            });
        }
        return new StagesApi(DEFAULT_CONFIG).stagesCaptchaCreate({
            captchaStageRequest: data as unknown as CaptchaStageRequest,
        });
    }

    handleProviderSelect: (provider: CaptchaProvider) => void = (provider) => {
        const prevProvider = this.selectedProvider;
        this.selectedProvider = provider;
        this.isCustomMode = provider === "custom";
        if (provider !== "custom") {
            const config = PROVIDER_CONFIGS[provider];
            const prevConfig = PROVIDER_CONFIGS[prevProvider];
            const form = this.querySelector("form");
            if (form) {
                const jsUrlInput = form.querySelector('input[name="jsUrl"]') as HTMLInputElement;
                const apiUrlInput = form.querySelector('input[name="apiUrl"]') as HTMLInputElement;
                if (jsUrlInput && (jsUrlInput.value === "" || jsUrlInput.value === prevConfig.jsUrl)) {
                    jsUrlInput.value = config.jsUrl;
                    jsUrlInput.dispatchEvent(new Event("input", { bubbles: true, composed: true }));
                }
                if (apiUrlInput && (apiUrlInput.value === "" || apiUrlInput.value === prevConfig.apiUrl)) {
                    apiUrlInput.value = config.apiUrl;
                    apiUrlInput.dispatchEvent(new Event("input", { bubbles: true, composed: true }));
                }
            }
        }
    }

    handleUrlChange: (e: Event) => void = (e) => {
        const input = e.target as HTMLInputElement;
        if (input.name === "jsUrl") {
            this.handleJsUrlChange(input.value);
        } else if (input.name === "apiUrl") {
            this.handleApiUrlChange(input.value);
        }
    }

    handleJsUrlChange: (value: string) => void = (value) => {
        const config = PROVIDER_CONFIGS[this.selectedProvider];
        if (!this.isCustomMode && value !== config.jsUrl) {
            this.isCustomMode = true;
            this.selectedProvider = "custom";
        }
    }

    handleApiUrlChange: (value: string) => void = (value) => {
        const config = PROVIDER_CONFIGS[this.selectedProvider];
        if (!this.isCustomMode && value !== config.apiUrl) {
            this.isCustomMode = true;
            this.selectedProvider = "custom";
        }
    }

    static get styles() {
        return [
            ...super.styles,
            css`
                .form-section {
                    margin-bottom: 2.5rem;
                }
                .form-section-header {
                    font-size: 1.2rem;
                    font-weight: 700;
                    margin-bottom: 1.25rem;
                    margin-top: 2rem;
                    color: var(--pf-global--Color--100);
                    letter-spacing: 0.01em;
                }
                .monospace {
                    font-family: var(--pf-global--font-family--monospace);
                    font-size: 0.93rem;
                }
                .pf-c-form__helper-text {
                    margin-top: 0.25rem;
                    font-size: 0.88rem;
                    color: var(--pf-global--Color--200);
                }
                .threshold-grid {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 1rem;
                }
                .options-grid {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 1rem;
                }
            `,
        ];
    }

    renderForm(): TemplateResult {
        if (!this.isConfigLoaded) {
            return html`<ak-empty-state loading></ak-empty-state>`;
        }
        // Build provider options for ak-radio-input
        const providerOptions = Object.entries(PROVIDER_CONFIGS).map(([key, config]) => ({
            label: config.name,
            value: key,
            description: html`<span>${config.description}${config.helpUrl ? html`<br /><a href="${config.helpUrl}" target="_blank" rel="noopener noreferrer">${msg("Learn more")} &rarr;</a>` : ""}</span>`
        }));
        return html`
            <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name || "")}"
                    class="pf-c-form-control"
                    required
                    placeholder=${msg("e.g. My CAPTCHA Stage")}
                />
                <p class="pf-c-form__helper-text">
                    ${msg("A unique, descriptive name for this stage.")}
                </p>
            </ak-form-element-horizontal>
            <ak-radio-input
                name="provider"
                label=${msg("CAPTCHA Provider")}
                .options=${providerOptions}
                .value=${this.selectedProvider}
                @input=${(e: CustomEvent) => this.handleProviderSelect(e.detail.value)}
            ></ak-radio-input>
            <ak-form-group .expanded=${true}>
                <span slot="header">${msg("Provider Configuration")}</span>
                <div slot="body">
                    <ak-form-element-horizontal label=${msg("JavaScript URL")} ?required=${true} name="jsUrl">
                        <input
                            type="url"
                            .value="${this.instance?.jsUrl ?? PROVIDER_CONFIGS[this.selectedProvider].jsUrl}"
                            class="pf-c-form-control monospace"
                            autocomplete="off"
                            spellcheck="false"
                            required
                            @input=${this.handleUrlChange}
                            placeholder=${msg("e.g. https://example.com/api.js")}
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("The URL for the CAPTCHA provider's JavaScript library. This is pre-filled based on your selection.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("API URL")} ?required=${true} name="apiUrl">
                        <input
                            type="url"
                            .value="${this.instance?.apiUrl ?? PROVIDER_CONFIGS[this.selectedProvider].apiUrl}"
                            class="pf-c-form-control monospace"
                            autocomplete="off"
                            spellcheck="false"
                            required
                            @input=${this.handleUrlChange}
                            placeholder=${msg("e.g. https://example.com/siteverify")}
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("The endpoint for verifying the CAPTCHA response. This is pre-filled based on your selection.")}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group .expanded=${true}>
                <span slot="header">${msg("Keys")}</span>
                <div slot="body">
                    <ak-form-element-horizontal label=${msg("Public Key")} ?required=${true} name="publicKey">
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.publicKey || "")}"
                            class="pf-c-form-control monospace"
                            autocomplete="off"
                            spellcheck="false"
                            required
                            placeholder=${msg("Enter your site key")}
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("The public site key provided by your CAPTCHA service.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("Private Key")} ?required=${!this.instance} name="privateKey">
                        <ak-hidden-text-input
                            name="privateKey"
                            .value=${this.instance ? "" : ""}
                            ?revealed=${this.instance === undefined}
                            placeholder=${msg("Enter your secret key")}
                            inputHint="code"
                            label=""
                            help=${this.instance
                                ? msg("Leave blank to keep the current private key.")
                                : msg("The secret key provided by your CAPTCHA service.")}
                        ></ak-hidden-text-input>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group .expanded=${false}>
                <span slot="header">${msg("Advanced Options")}</span>
                <div slot="body">
                    <div style="margin-bottom: 1.5rem;">
                        <div style="font-weight: 600; margin-bottom: 0.5rem;">${msg("Score Thresholds")}</div>
                        <div class="threshold-grid">
                            <ak-number-input
                                label=${msg("Minimum Score")}
                                required
                                name="scoreMinThreshold"
                                value="${ifDefined(this.instance?.scoreMinThreshold ?? 0.5)}"
                                help=${msg("The minimum score (0.0-1.0) for a user to be considered human.")}
                                min="0"
                                max="1"
                                step="0.1"
                            ></ak-number-input>
                            <ak-number-input
                                label=${msg("Maximum Score")}
                                required
                                name="scoreMaxThreshold"
                                value="${ifDefined(this.instance?.scoreMaxThreshold ?? 1.0)}"
                                help=${msg("The maximum score (0.0-1.0) for a user to be considered human.")}
                                min="0"
                                max="1"
                                step="0.1"
                            ></ak-number-input>
                        </div>
                        <p class="pf-c-form__helper-text" style="margin-top: 1rem;">
                            ${msg("These thresholds define the range of scores considered valid. A higher minimum increases security but may affect user experience.")}
                        </p>
                    </div>
                    <div>
                        <div style="font-weight: 600; margin-bottom: 0.5rem;">${msg("Behavior")}</div>
                        <div class="options-grid">
                            <ak-switch-input
                                name="interactive"
                                label=${msg("Interactive Mode")}
                                ?checked=${this.instance?.interactive ?? false}
                                help=${msg("Requires direct user interaction with the CAPTCHA. Non-interactive mode runs invisibly in the background.")}
                            ></ak-switch-input>
                            <ak-switch-input
                                name="errorOnInvalidScore"
                                label=${msg("Error on Invalid Score")}
                                ?checked=${this.instance?.errorOnInvalidScore ?? true}
                                help=${msg("When enabled, users who fail the CAPTCHA will be shown an error message. When disabled, the flow will continue but the 'passing' status will be set to 'false'.")}
                            ></ak-switch-input>
                        </div>
                    </div>
                </div>
            </ak-form-group>
            <style>
            /* Fix spacing between required asterisk and input fields */
            ak-form-element-horizontal label[required]::after {
                margin-left: 0.25em !important;
            }
            ak-form-element-horizontal .pf-c-form-control {
                margin-left: 0 !important;
            }
            </style>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-captcha-form": CaptchaStageForm;
    }
}

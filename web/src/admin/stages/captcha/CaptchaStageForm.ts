import "#components/ak-number-input";
import "#components/ak-secret-text-input";
import "#components/ak-switch-input";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";

import { DEFAULT_CONFIG } from "#common/api/config";

import { BaseStageForm } from "#admin/stages/BaseStageForm";

import { CaptchaStage, CaptchaStageRequest, StagesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

interface CaptchaProviderPreset {
    label: string;
    jsUrl: string;
    apiUrl: string;
    interactive: boolean;
    supportsScore: boolean;
    score?: { min: number; max: number };
    help: {
        pubText: string;
        pubLinkText: string;
        pubLinkUrl: string;
        privText: string;
        privLinkText: string;
        privLinkUrl: string;
    };
}

/**
 * Provider presets for common CAPTCHA services.
 * Each preset contains default URLs, settings, and help text with links to provider dashboards.
 * When a provider is selected, these values auto-fill the form but remain editable.
 */
const CAPTCHA_PROVIDERS: Record<string, CaptchaProviderPreset> = {
    recaptcha_v2: {
        label: "Google reCAPTCHA v2",
        jsUrl: "https://www.recaptcha.net/recaptcha/api.js",
        apiUrl: "https://www.recaptcha.net/recaptcha/api/siteverify",
        interactive: true,
        supportsScore: false,
        help: {
            pubText: "Site key for your CAPTCHA provider. Get keys from the",
            pubLinkText: "reCAPTCHA admin console",
            pubLinkUrl: "https://www.google.com/recaptcha/admin",
            privText: "Secret key for your CAPTCHA provider. Get keys from the",
            privLinkText: "reCAPTCHA admin console",
            privLinkUrl: "https://www.google.com/recaptcha/admin",
        },
    },
    recaptcha_v3: {
        label: "Google reCAPTCHA v3",
        jsUrl: "https://www.recaptcha.net/recaptcha/api.js",
        apiUrl: "https://www.recaptcha.net/recaptcha/api/siteverify",
        interactive: false,
        supportsScore: true,
        score: { min: 0.5, max: 1.0 },
        help: {
            pubText: "Site key for your CAPTCHA provider. Get keys from the",
            pubLinkText: "reCAPTCHA admin console",
            pubLinkUrl: "https://www.google.com/recaptcha/admin",
            privText: "Secret key for your CAPTCHA provider. Get keys from the",
            privLinkText: "reCAPTCHA admin console",
            privLinkUrl: "https://www.google.com/recaptcha/admin",
        },
    },
    recaptcha_enterprise: {
        label: "Google reCAPTCHA Enterprise",
        jsUrl: "https://www.recaptcha.net/recaptcha/enterprise.js",
        apiUrl: "https://www.recaptcha.net/recaptcha/api/siteverify",
        interactive: false,
        supportsScore: true,
        score: { min: 0.5, max: 1.0 },
        help: {
            pubText: "Site key for your CAPTCHA provider. Get keys from",
            pubLinkText: "Google Cloud reCAPTCHA Enterprise",
            pubLinkUrl: "https://cloud.google.com/recaptcha-enterprise",
            privText: "Secret key for your CAPTCHA provider. Get keys from",
            privLinkText: "Google Cloud reCAPTCHA Enterprise",
            privLinkUrl: "https://cloud.google.com/recaptcha-enterprise",
        },
    },
    hcaptcha: {
        label: "hCaptcha",
        jsUrl: "https://js.hcaptcha.com/1/api.js",
        apiUrl: "https://api.hcaptcha.com/siteverify",
        interactive: true,
        supportsScore: true,
        score: { min: 0.0, max: 0.5 },
        help: {
            pubText: "Site key for your CAPTCHA provider. Get keys from the",
            pubLinkText: "hCaptcha dashboard",
            pubLinkUrl: "https://dashboard.hcaptcha.com",
            privText: "Secret key for your CAPTCHA provider. Get keys from the",
            privLinkText: "hCaptcha dashboard",
            privLinkUrl: "https://dashboard.hcaptcha.com",
        },
    },
    turnstile: {
        label: "Cloudflare Turnstile",
        jsUrl: "https://challenges.cloudflare.com/turnstile/v0/api.js",
        apiUrl: "https://challenges.cloudflare.com/turnstile/v0/siteverify",
        interactive: true,
        supportsScore: false,
        help: {
            pubText: "Site key for your CAPTCHA provider. Get keys from the",
            pubLinkText: "Cloudflare dashboard",
            pubLinkUrl: "https://dash.cloudflare.com",
            privText: "Secret key for your CAPTCHA provider. Get keys from the",
            privLinkText: "Cloudflare dashboard",
            privLinkUrl: "https://dash.cloudflare.com",
        },
    },
    custom: {
        label: "Custom",
        jsUrl: "https://www.recaptcha.net/recaptcha/api.js",
        apiUrl: "https://www.recaptcha.net/recaptcha/api/siteverify",
        interactive: false,
        supportsScore: true,
        score: { min: 0.5, max: 1.0 },
        help: {
            pubText: "Site key from your CAPTCHA provider.",
            pubLinkText: "",
            pubLinkUrl: "",
            privText: "Secret key from your CAPTCHA provider.",
            privLinkText: "",
            privLinkUrl: "",
        },
    },
};

@customElement("ak-stage-captcha-form")
export class CaptchaStageForm extends BaseStageForm<CaptchaStage> {
    @state()
    selectedProvider = "custom";

    @state()
    currentPreset: CaptchaProviderPreset = CAPTCHA_PROVIDERS.custom;

    loadInstance(pk: string): Promise<CaptchaStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesCaptchaRetrieve({
            stageUuid: pk,
        });
    }

    /**
     * Detect which provider preset matches the current instance by comparing URLs.
     * This allows the form to show the correct provider in the dropdown when editing
     * an existing CAPTCHA stage. Falls back to "custom" if no match is found.
     */
    detectProviderFromInstance(): string {
        if (!this.instance) return "custom";

        for (const [key, preset] of Object.entries(CAPTCHA_PROVIDERS)) {
            if (this.instance.jsUrl === preset.jsUrl && this.instance.apiUrl === preset.apiUrl) {
                return key;
            }
        }
        return "custom";
    }

    firstUpdated(changedProperties: Map<PropertyKey, unknown>): void {
        super.firstUpdated(changedProperties);
        this.selectedProvider = this.detectProviderFromInstance();
        this.currentPreset = CAPTCHA_PROVIDERS[this.selectedProvider];
    }

    /**
     * Handle provider dropdown selection change.
     * Updates the preset and auto-fills form fields with provider-specific defaults.
     * Uses direct DOM manipulation because the form fields are rendered in the light DOM
     * and need to be updated now to reflect the new provider settings.
     */
    handleProviderChange(e: Event): void {
        const select = e.target as HTMLSelectElement;
        this.selectedProvider = select.value;
        this.currentPreset = CAPTCHA_PROVIDERS[this.selectedProvider];

        // Auto-fill the URLs and interactive setting from the selected preset
        const jsUrlInput = this.shadowRoot?.querySelector(
            'input[name="jsUrl"]',
        ) as HTMLInputElement;
        const apiUrlInput = this.shadowRoot?.querySelector(
            'input[name="apiUrl"]',
        ) as HTMLInputElement;
        const interactiveSwitch = this.shadowRoot?.querySelector(
            'ak-switch-input[name="interactive"]',
        ) as HTMLInputElement;

        if (jsUrlInput) jsUrlInput.value = this.currentPreset.jsUrl;
        if (apiUrlInput) apiUrlInput.value = this.currentPreset.apiUrl;
        if (interactiveSwitch) interactiveSwitch.checked = this.currentPreset.interactive;

        // Update score thresholds if preset has defaults
        if (this.currentPreset.score) {
            const minScoreInput = this.shadowRoot?.querySelector(
                'ak-number-input[name="scoreMinThreshold"]',
            ) as HTMLInputElement;
            const maxScoreInput = this.shadowRoot?.querySelector(
                'ak-number-input[name="scoreMaxThreshold"]',
            ) as HTMLInputElement;

            if (minScoreInput) minScoreInput.value = this.currentPreset.score.min.toString();
            if (maxScoreInput) maxScoreInput.value = this.currentPreset.score.max.toString();
        }

        // Trigger re-render to update help text and conditional sections
        this.requestUpdate();
    }

    async send(data: CaptchaStage): Promise<CaptchaStage> {
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

    renderProviderSelector(): TemplateResult {
        return html`<ak-form-element-horizontal label=${msg("Provider Type")} name="providerType">
            <select
                class="pf-c-form-control"
                @change=${this.handleProviderChange}
                .value=${this.selectedProvider}
            >
                ${Object.entries(CAPTCHA_PROVIDERS).map(
                    ([key, preset]) =>
                        html`<option value=${key} ?selected=${this.selectedProvider === key}>
                            ${preset.label}
                        </option>`,
                )}
            </select>
            <p class="pf-c-form__helper-text">
                ${msg(
                    "Select a CAPTCHA provider. URLs and settings will be automatically configured, but can be customized below.",
                )}
            </p>
        </ak-form-element-horizontal>`;
    }

    renderKeyFields(): TemplateResult {
        // bighelp is an extended help property on HorizontalLightComponent that accepts
        // TemplateResult for rich HTML content (like links), whereas the standard help
        // property only accepts plain strings
        const privKeyHelp = html`<p class="pf-c-form__helper-text">
            ${msg(this.currentPreset.help.privText)}
            ${this.currentPreset.help.privLinkUrl
                ? html`<a
                          target="_blank"
                          rel="noopener noreferrer"
                          href=${this.currentPreset.help.privLinkUrl}
                      >
                          ${this.currentPreset.help.privLinkText} </a
                      >.`
                : ""}
        </p>`;

        return html`
            <ak-form-element-horizontal label=${msg("Public Key")} required name="publicKey">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.publicKey || "")}"
                    class="pf-c-form-control pf-m-monospace"
                    autocomplete="off"
                    spellcheck="false"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${msg(this.currentPreset.help.pubText)}
                    ${this.currentPreset.help.pubLinkUrl
                        ? html`<a
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  href=${this.currentPreset.help.pubLinkUrl}
                              >
                                  ${this.currentPreset.help.pubLinkText} </a
                              >.`
                        : ""}
                </p>
            </ak-form-element-horizontal>

            <ak-secret-text-input
                name="privateKey"
                label=${msg("Private Key")}
                input-hint="code"
                ?required=${!this.instance}
                ?revealed=${!this.instance}
                .bighelp=${privKeyHelp}
            ></ak-secret-text-input>
        `;
    }

    renderScoreConfiguration(): TemplateResult {
        if (!this.currentPreset.supportsScore) {
            return html`<ak-form-group open label="${msg("Score Configuration")}">
                <div class="pf-c-form">
                    <p class="pf-c-form__helper-text">
                        ${msg(
                            "This CAPTCHA provider does not support scoring. Score thresholds will be ignored.",
                        )}
                    </p>
                    <input type="hidden" name="scoreMinThreshold" value="0" />
                    <input type="hidden" name="scoreMaxThreshold" value="1" />
                    <input type="hidden" name="errorOnInvalidScore" value="false" />
                </div>
            </ak-form-group>`;
        }

        return html`<ak-form-group open label="${msg("Score Configuration")}">
            <div class="pf-c-form">
                <ak-number-input
                    label=${msg("Score Minimum Threshold")}
                    required
                    name="scoreMinThreshold"
                    value="${ifDefined(
                        this.instance?.scoreMinThreshold ?? this.currentPreset.score?.min ?? 0.5,
                    )}"
                    help=${msg(
                        "Minimum required score to allow continuing. Lower scores indicate more suspicious behavior.",
                    )}
                ></ak-number-input>
                <ak-number-input
                    label=${msg("Score Maximum Threshold")}
                    required
                    name="scoreMaxThreshold"
                    value="${ifDefined(
                        this.instance?.scoreMaxThreshold ?? this.currentPreset.score?.max ?? 1.0,
                    )}"
                    help=${msg(
                        "Maximum allowed score to allow continuing. Set to -1 to disable upper bound checking.",
                    )}
                ></ak-number-input>
                <ak-switch-input
                    ?checked=${!!(this.instance?.errorOnInvalidScore ?? true)}
                    name="errorOnInvalidScore"
                    label=${msg("Error on Invalid Score")}
                    help=${msg(
                        "When enabled and the score is outside the threshold, the user will not be able to continue. When disabled, the user can continue and the score can be used in policies.",
                    )}
                ></ak-switch-input>
            </div>
        </ak-form-group>`;
    }

    renderAdvancedSettings(): TemplateResult {
        return html`<ak-form-group label="${msg("Advanced Settings")}">
            <div class="pf-c-form">
                <ak-form-element-horizontal label=${msg("JavaScript URL")} required name="jsUrl">
                    <input
                        type="url"
                        value="${ifDefined(this.instance?.jsUrl || this.currentPreset.jsUrl)}"
                        class="pf-c-form-control pf-m-monospace"
                        autocomplete="off"
                        spellcheck="false"
                        required
                    />
                    <p class="pf-c-form__helper-text">
                        ${msg(
                            "URL to fetch the CAPTCHA JavaScript library from. Automatically set based on provider selection but can be customized.",
                        )}
                    </p>
                </ak-form-element-horizontal>
                <ak-form-element-horizontal
                    label=${msg("API Verification URL")}
                    required
                    name="apiUrl"
                >
                    <input
                        type="url"
                        value="${ifDefined(this.instance?.apiUrl || this.currentPreset.apiUrl)}"
                        class="pf-c-form-control pf-m-monospace"
                        autocomplete="off"
                        spellcheck="false"
                        required
                    />
                    <p class="pf-c-form__helper-text">
                        ${msg(
                            "URL used to validate CAPTCHA response on the backend. Automatically set based on provider selection but can be customized.",
                        )}
                    </p>
                </ak-form-element-horizontal>
            </div>
        </ak-form-group>`;
    }

    renderForm(): TemplateResult {
        return html`
            <span>
                ${msg(
                    "This stage checks the user's current session against a CAPTCHA service to prevent automated abuse.",
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

            <ak-form-group open label="${msg("CAPTCHA Provider")}">
                <div class="pf-c-form">
                    ${this.renderProviderSelector()} ${this.renderKeyFields()}
                    <ak-switch-input
                        name="interactive"
                        label=${msg("Interactive")}
                        ?checked="${this.instance?.interactive ?? this.currentPreset.interactive}"
                        help=${msg(
                            "Enable this if the CAPTCHA requires user interaction (clicking checkbox, solving puzzles, etc.). Required for reCAPTCHA v2, hCaptcha interactive mode, and Cloudflare Turnstile.",
                        )}
                    ></ak-switch-input>
                </div>
            </ak-form-group>

            ${this.renderScoreConfiguration()} ${this.renderAdvancedSettings()}
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-captcha-form": CaptchaStageForm;
    }
}

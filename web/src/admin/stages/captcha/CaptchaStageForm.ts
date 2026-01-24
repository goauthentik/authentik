import "#components/ak-number-input";
import "#components/ak-secret-text-input";
import "#components/ak-switch-input";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";

import { DEFAULT_CONFIG } from "#common/api/config";

import { BaseStageForm } from "#admin/stages/BaseStageForm";

import { CaptchaStage, CaptchaStageRequest, StagesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, PropertyValues, TemplateResult } from "lit";
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
        keyLinkText: string;
        keyLinkUrl: string;
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
            keyLinkText: msg("the reCAPTCHA admin console"),
            keyLinkUrl: "https://www.google.com/recaptcha/admin",
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
            keyLinkText: msg("the reCAPTCHA admin console"),
            keyLinkUrl: "https://www.google.com/recaptcha/admin",
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
            keyLinkText: msg("Google Cloud reCAPTCHA Enterprise"),
            keyLinkUrl: "https://cloud.google.com/recaptcha-enterprise",
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
            keyLinkText: msg("the hCaptcha dashboard"),
            keyLinkUrl: "https://dashboard.hcaptcha.com",
        },
    },
    turnstile: {
        label: "Cloudflare Turnstile",
        jsUrl: "https://challenges.cloudflare.com/turnstile/v0/api.js",
        apiUrl: "https://challenges.cloudflare.com/turnstile/v0/siteverify",
        interactive: true,
        supportsScore: false,
        help: {
            keyLinkText: msg("the Cloudflare dashboard"),
            keyLinkUrl: "https://dash.cloudflare.com",
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
            keyLinkText: "",
            keyLinkUrl: "",
        },
    },
};

@customElement("ak-stage-captcha-form")
export class CaptchaStageForm extends BaseStageForm<CaptchaStage> {
    @state()
    protected selectedProvider = "recaptcha_v2";

    currentPreset: CaptchaProviderPreset = CAPTCHA_PROVIDERS.recaptcha_v2;

    public override reset(): void {
        super.reset();

        this.selectedProvider = "custom";
        this.currentPreset = CAPTCHA_PROVIDERS.custom;
    }

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

    willUpdate(changed: PropertyValues<this>): void {
        super.willUpdate(changed);
        if (changed.has("instance")) {
            this.selectedProvider = this.detectProviderFromInstance();
            this.currentPreset = CAPTCHA_PROVIDERS[this.selectedProvider];
        }
    }

    /**
     * Get localized help text for public/private key fields.
     * These methods return msg() calls with string literals instead of
     * storing translatable strings in the preset objects, which would break i18n.
     * The Lit localize library requires msg() to be called with string literals at
     * compile time so it can extract them for translation.
     */
    getPublicKeyHelpText(anchor?: TemplateResult): string | TemplateResult {
        return anchor
            ? msg(html`Site key from your CAPTCHA provider. Get keys from ${anchor}`)
            : msg("Site key from your CAPTCHA provider.");
    }

    getPrivateKeyHelpText(anchor?: TemplateResult): string | TemplateResult {
        return anchor
            ? msg(html`Secret key from your CAPTCHA provider. Get keys from ${anchor}`)
            : msg("Secret key from your CAPTCHA provider.");
    }

    /**
     * Renders help text wrapped in the PF helper text element.
     * Used for form fields that need to display help text with optional anchor links.
     */
    renderHelpText(content: string | TemplateResult): TemplateResult {
        return html`<p class="pf-c-form__helper-text">${content}</p>`;
    }

    /**
     * Get the form values to display, with clear precedence:
     * 1. If editing an existing instance, use instance values
     * 2. Otherwise, use the current preset defaults
     */
    getFormValues() {
        if (this.instance) {
            return {
                jsUrl: this.instance.jsUrl,
                apiUrl: this.instance.apiUrl,
                interactive: this.instance.interactive,
                scoreMinThreshold: this.instance.scoreMinThreshold,
                scoreMaxThreshold: this.instance.scoreMaxThreshold,
                errorOnInvalidScore: this.instance.errorOnInvalidScore ?? true,
            };
        }
        return {
            jsUrl: this.currentPreset.jsUrl,
            apiUrl: this.currentPreset.apiUrl,
            interactive: this.currentPreset.interactive,
            scoreMinThreshold: this.currentPreset.score?.min ?? 0.5,
            scoreMaxThreshold: this.currentPreset.score?.max ?? 1.0,
            errorOnInvalidScore: true,
        };
    }

    /**
     * Handle provider dropdown selection change.
     * Updates the preset, which triggers a re-render with new default values.
     */
    handleProviderChange(e: Event): void {
        const select = e.target as HTMLSelectElement;
        this.selectedProvider = select.value;
        this.currentPreset = CAPTCHA_PROVIDERS[this.selectedProvider];
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
            <select class="pf-c-form-control" @change=${this.handleProviderChange}>
                ${Object.entries(CAPTCHA_PROVIDERS).map(
                    ([key, preset]) =>
                        html`<option value=${key} ?selected=${key === this.selectedProvider}>
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
        const keyLink =
            this.currentPreset.help.keyLinkUrl && this.currentPreset.help.keyLinkText
                ? html`<a
                          target="_blank"
                          rel="noopener noreferrer"
                          href=${this.currentPreset.help.keyLinkUrl}
                      >
                          ${this.currentPreset.help.keyLinkText} </a
                      >.`
                : undefined;

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
                ${this.renderHelpText(this.getPublicKeyHelpText(keyLink))}
            </ak-form-element-horizontal>

            <ak-secret-text-input
                name="privateKey"
                label=${msg("Private Key")}
                input-hint="code"
                ?required=${!this.instance}
                ?revealed=${!this.instance}
                .bighelp=${this.renderHelpText(this.getPrivateKeyHelpText(keyLink))}
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

        const formValues = this.getFormValues();
        return html`<ak-form-group open label="${msg("Score Configuration")}">
            <div class="pf-c-form">
                <ak-number-input
                    label=${msg("Score Minimum Threshold")}
                    required
                    name="scoreMinThreshold"
                    value="${ifDefined(formValues.scoreMinThreshold)}"
                    help=${msg(
                        "Minimum required score to allow continuing. Lower scores indicate more suspicious behavior.",
                    )}
                ></ak-number-input>
                <ak-number-input
                    label=${msg("Score Maximum Threshold")}
                    required
                    name="scoreMaxThreshold"
                    value="${ifDefined(formValues.scoreMaxThreshold)}"
                    help=${msg(
                        "Maximum allowed score to allow continuing. Set to -1 to disable upper bound checking.",
                    )}
                ></ak-number-input>
                <ak-switch-input
                    ?checked=${formValues.errorOnInvalidScore}
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
        const formValues = this.getFormValues();
        return html`<ak-form-group label="${msg("Advanced Settings")}">
            <div class="pf-c-form">
                <ak-form-element-horizontal label=${msg("JavaScript URL")} required name="jsUrl">
                    <input
                        type="url"
                        value="${ifDefined(formValues.jsUrl)}"
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
                        value="${ifDefined(formValues.apiUrl)}"
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

    protected override renderForm(): TemplateResult {
        const formValues = this.getFormValues();
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
                        ?checked="${formValues.interactive}"
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

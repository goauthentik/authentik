import "#components/ak-number-input";
import "#components/ak-secret-text-input";
import "#components/ak-switch-input";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";

import { DEFAULT_CONFIG } from "#common/api/config";

import { BaseStageForm } from "#admin/stages/BaseStageForm";

import { CaptchaStage, CaptchaStageRequest, StagesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult, PropertyValues } from "lit";
import { customElement, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-stage-captcha-form")
export class CaptchaStageForm extends BaseStageForm<CaptchaStage> {
    @state()
    private selectedPreset: PresetKey = "custom";

    @state()
    private revealPrivateKey = true;

    private hasInitializedInstance = false;

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
        }
        return new StagesApi(DEFAULT_CONFIG).stagesCaptchaCreate({
            captchaStageRequest: data as unknown as CaptchaStageRequest,
        });
    }

    protected updated(_changedProperties: PropertyValues<this>): void {
        if (!this.hasInitializedInstance && this.instance !== undefined) {
            this.hasInitializedInstance = true;
            if ((this.instance as Partial<CaptchaStage>).pk) {
                this.revealPrivateKey = false;
            }
        }
    }

    renderForm(): TemplateResult {
        const current = this.instance ?? ({} as Partial<CaptchaStage>);
        const updateEnterpriseJsFromPublicKey = (pub: string | undefined) => {
            if (this.selectedPreset !== "recaptcha_enterprise") return;
            const interactive = this.instance?.interactive ?? false;
            const base = PRESETS.recaptcha_enterprise.jsUrl;
            if (!interactive && pub && pub.length > 0) {
                this.instance = {
                    ...(this.instance ?? ({} as CaptchaStage)),
                    jsUrl: `${base}?render=${encodeURIComponent(pub)}`,
                } as CaptchaStage;
            } else if (!interactive && (!pub || pub.length === 0)) {
                // Reset to base if no key present
                this.instance = {
                    ...(this.instance ?? ({} as CaptchaStage)),
                    jsUrl: base,
                } as CaptchaStage;
            }
        };

        const onPresetChange = (preset: PresetKey) => {
            this.selectedPreset = preset;
            if (preset === "custom") return;
            const p = PRESETS[preset];
            // Merge into instance to cause a re-render with the preset defaults.
            this.instance = {
                ...(this.instance ?? ({} as CaptchaStage)),
                jsUrl: p.jsUrl,
                apiUrl: p.apiUrl,
                interactive: p.interactive,
                // For providers without scoring, default to -1 to disable score validation.
                scoreMinThreshold: p.score?.min ?? (p.supportsScore ? 0.5 : -1),
                scoreMaxThreshold: p.score?.max ?? (p.supportsScore ? 1.0 : -1),
            } as CaptchaStage;

            if (preset === "recaptcha_enterprise") {
                updateEnterpriseJsFromPublicKey(this.instance?.publicKey);
            }
        };

        const disableScoreInputs = (() => {
            // Disable when preset explicitly says no score, or when Turnstile is detected.
            if (this.selectedPreset in PRESETS) {
                return !PRESETS[this.selectedPreset as Exclude<PresetKey, "auto" | "custom">]
                    .supportsScore;
            }
            return false;
        })();

        return html` <span>
                ${msg(
                    "This stage checks the user's current session against the Google reCaptcha (or compatible) service.",
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
            <ak-form-group open label="${msg("Stage-specific settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal label=${msg("Provider preset")} name="provider">
                        <select
                            class="pf-c-form-control"
                            @change=${(e: Event) =>
                                onPresetChange((e.target as HTMLSelectElement).value as PresetKey)}
                        >
                            ${renderPresetOptions(this.selectedPreset)}
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Choose a provider to prefill defaults. You can still adjust fields below.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Public Key")}
                        required
                        name="publicKey"
                    >
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.publicKey || "")}"
                            class="pf-c-form-control pf-m-monospace"
                            autocomplete="off"
                            spellcheck="false"
                            required
                            @input=${(ev: InputEvent) => {
                                const v = (ev.target as HTMLInputElement).value;
                                this.instance = {
                                    ...(this.instance ?? ({} as CaptchaStage)),
                                    publicKey: v,
                                } as CaptchaStage;
                                updateEnterpriseJsFromPublicKey(v);
                            }}
                        />
                        <p class="pf-c-form__helper-text">
                            ${providerPublicKeyHelp(this.selectedPreset)}
                        </p>
                    </ak-form-element-horizontal>

                    <ak-secret-text-input
                        name="privateKey"
                        label=${msg("Private Key")}
                        input-hint="code"
                        required
                        ?revealed=${this.revealPrivateKey}
                        help=${providerPrivateKeyHelp(this.selectedPreset)}
                    ></ak-secret-text-input>

                    <ak-switch-input
                        name="interactive"
                        label=${msg("Interactive")}
                        ?checked=${this.instance?.interactive}
                        help=${msg(
                            "Enable this flag if the configured captcha requires User-interaction. Required for reCAPTCHA v2, hCaptcha and Cloudflare Turnstile.",
                        )}
                        @change=${() => updateEnterpriseJsFromPublicKey(this.instance?.publicKey)}
                    >
                    </ak-switch-input>
                    <ak-form-element-horizontal label=${msg("JS URL")} required name="jsUrl">
                        <input
                            type="url"
                            value="${ifDefined(this.instance?.jsUrl || "" )}"
                            class="pf-c-form-control pf-m-monospace"
                            autocomplete="off"
                            spellcheck="false"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "URL to fetch JavaScript from. Can be replaced with any compatible alternative.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("API URL")} required name="apiUrl">
                        <input
                            type="url"
                            value="${ifDefined(this.instance?.apiUrl || "" )}"
                            class="pf-c-form-control pf-m-monospace"
                            autocomplete="off"
                            spellcheck="false"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "URL used to validate captcha response. Can be replaced with any compatible alternative.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-number-input
                        label=${msg("Score minimum threshold")}
                        required
                        name="scoreMinThreshold"
                        value="${ifDefined(this.instance?.scoreMinThreshold ?? 0.5)}"
                        ?disabled=${disableScoreInputs}
                        help=${msg("Minimum required score to allow continuing")}
                    ></ak-number-input>
                    <ak-number-input
                        label=${msg("Score maximum threshold")}
                        required
                        name="scoreMaxThreshold"
                        value="${ifDefined(this.instance?.scoreMaxThreshold ?? -1)}"
                        ?disabled=${disableScoreInputs}
                        help=${msg("Maximum allowed score to allow continuing")}
                    ></ak-number-input>
                    <ak-form-element-horizontal name="errorOnInvalidScore">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${this.instance?.errorOnInvalidScore ?? true}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label">${msg("Error on invalid score")}</span>
                        </label>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "When enabled and the resultant score is outside the threshold, the user will not be able to continue. When disabled, the user will be able to continue and the score can be used in policies to customize further stages.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-captcha-form": CaptchaStageForm;
    }
}

type PresetKey =
    | "custom"
    | "recaptcha_v2"
    | "recaptcha_v3"
    | "recaptcha_enterprise"
    | "hcaptcha"
    | "turnstile";

type Preset = {
    label: string;
    jsUrl: string;
    apiUrl: string;
    interactive: boolean;
    supportsScore: boolean;
    score?: { min: number; max: number };
    help?: { pub: string; priv: string };
};

const PRESETS: Record<Exclude<PresetKey, "custom">, Preset> = {
    recaptcha_v2: {
        label: "Google reCAPTCHA v2",
        jsUrl: "https://www.recaptcha.net/recaptcha/api.js",
        apiUrl: "https://www.recaptcha.net/recaptcha/api/siteverify",
        interactive: true,
        supportsScore: false,
        help: {
            pub: "Public key, acquired from https://www.google.com/recaptcha/admin.",
            priv: "Private key, acquired from https://www.google.com/recaptcha/admin.",
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
            pub: "Public key, acquired from https://www.google.com/recaptcha/admin.",
            priv: "Private key, acquired from https://www.google.com/recaptcha/admin.",
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
            pub: "Public key, acquired from https://cloud.google.com/recaptcha-enterprise.",
            priv: "Private key, acquired from https://cloud.google.com/recaptcha-enterprise.",
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
            pub: "Public key, acquired from https://dashboard.hcaptcha.com/.",
            priv: "Private key, acquired from https://dashboard.hcaptcha.com/.",
        },
    },
    turnstile: {
        label: "Cloudflare Turnstile",
        jsUrl: "https://challenges.cloudflare.com/turnstile/v0/api.js",
        apiUrl: "https://challenges.cloudflare.com/turnstile/v0/siteverify",
        interactive: true,
        supportsScore: false,
        help: {
            pub: "Site key, from Cloudflare Turnstile",
            priv: "Secret key, from Cloudflare Turnstile",
        },
    },
};

function renderPresetOptions(selected: PresetKey) {
    const effective = selected;
    const option = (value: PresetKey, label: string) =>
        html`<option value="${value}" ?selected=${effective === value}>${label}</option>`;
    return html`${option("recaptcha_v2", PRESETS.recaptcha_v2.label)}
    ${option("recaptcha_v3", PRESETS.recaptcha_v3.label)}
    ${option("recaptcha_enterprise", PRESETS.recaptcha_enterprise.label)}
    ${option("hcaptcha", PRESETS.hcaptcha.label)} ${option("turnstile", PRESETS.turnstile.label)}
    ${option("custom", "Custom")}`;
}

function providerPublicKeyHelp(preset: PresetKey): string {
    if (preset === "custom") {
        return msg("Public key, acquired from your captcha provider.");
    }
    return PRESETS[preset]?.help?.pub ?? msg("Public key, acquired from your captcha provider.");
}

function providerPrivateKeyHelp(preset: PresetKey): string {
    if (preset === "custom") {
        return msg("Private key, acquired from your captcha provider.");
    }
    return PRESETS[preset]?.help?.priv ?? msg("Private key, acquired from your captcha provider.");
}

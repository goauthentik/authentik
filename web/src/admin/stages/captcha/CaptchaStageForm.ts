import "#components/ak-text-input";
import "#components/ak-number-input";
import "#components/ak-secret-text-input";
import "#components/ak-switch-input";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/Alert";

import { DEFAULT_CONFIG } from "#common/api/config";

import { Level } from "#elements/Alert";
import { SlottedTemplateResult } from "#elements/types";

import { BaseStageForm } from "#admin/stages/BaseStageForm";
import {
    CAPTCHA_PROVIDERS,
    CaptchaProviderKey,
    CaptchaProviderKeys,
    CaptchaProviderPreset,
    detectProviderFromInstance,
    pluckFormValues,
} from "#admin/stages/captcha/shared";
import Styles from "#admin/stages/captcha/styles.css";

import {
    CaptchaStage,
    CaptchaStageRequest,
    PatchedCaptchaStageRequest,
    StagesApi,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, PropertyValues } from "lit";
import { customElement, state } from "lit/decorators.js";
import { guard } from "lit/directives/guard.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-stage-captcha-form")
export class CaptchaStageForm extends BaseStageForm<CaptchaStage> {
    public static override readonly styles = [...super.styles, Styles];

    #api = new StagesApi(DEFAULT_CONFIG);

    //#region Lifecycle

    @state()
    protected selectedProvider: CaptchaProviderKey = "recaptcha_v2";

    #currentPreset: CaptchaProviderPreset = CAPTCHA_PROVIDERS.recaptcha_v2;

    public override reset(): void {
        super.reset();

        this.selectedProvider = "custom";
        this.#currentPreset = CAPTCHA_PROVIDERS.custom;
    }

    protected loadInstance(pk: string): Promise<CaptchaStage> {
        return this.#api.stagesCaptchaRetrieve({
            stageUuid: pk,
        });
    }

    protected override willUpdate(changed: PropertyValues<this>): void {
        super.willUpdate(changed);

        if (changed.has("instance")) {
            this.selectedProvider = detectProviderFromInstance(this.instance);
            this.#currentPreset = CAPTCHA_PROVIDERS[this.selectedProvider];
        }
    }

    /**
     * Handle provider dropdown selection change.
     * Updates the preset, which triggers a re-render with new default values.
     */
    #providerChangeListener(e: Event): void {
        const select = e.target as HTMLSelectElement;
        this.selectedProvider = select.value as CaptchaProviderKey;
        this.#currentPreset = CAPTCHA_PROVIDERS[this.selectedProvider];
    }

    public async send(
        data: CaptchaStageRequest | PatchedCaptchaStageRequest,
    ): Promise<CaptchaStage> {
        if (this.instance) {
            return this.#api.stagesCaptchaPartialUpdate({
                stageUuid: this.instance.pk || "",
                patchedCaptchaStageRequest: data,
            });
        }

        return this.#api.stagesCaptchaCreate({
            captchaStageRequest: data as CaptchaStageRequest,
        });
    }

    //#endregion

    //#region Rendering

    protected renderProviderSelector(): SlottedTemplateResult {
        return html`<ak-form-element-horizontal label=${msg("Provider Type")} name="providerType">
            <select class="pf-c-form-control" @change=${this.#providerChangeListener}>
                ${Array.from(CaptchaProviderKeys, (key) => {
                    const preset = CAPTCHA_PROVIDERS[key];

                    return html`<option value=${key} ?selected=${key === this.selectedProvider}>
                        ${preset.formatDisplayName()}
                    </option>`;
                })}
            </select>
            <p class="pf-c-form__helper-text">
                ${msg(
                    "You can select from popular providers with preset configurations or choose a custom setup to specify your own endpoints and keys.",
                )}
            </p>

            ${guard([this.#currentPreset], () => {
                const { formatAPISource, keyURL } = this.#currentPreset;

                if (!formatAPISource || !keyURL) {
                    return null;
                }

                return html`<ak-alert level=${Level.Info} icon="fa-key">
                    ${msg(
                        html`API keys can be obtained from the
                        ${html`<a target="_blank" rel="noopener noreferrer" href=${keyURL}
                                >${formatAPISource()}</a
                            >.`}`,
                        {
                            id: "captcha.provider-link",
                            desc: "Supplementary help text with link to provider dashboard.",
                        },
                    )}
                </ak-alert>`;
            })}
        </ak-form-element-horizontal>`;
    }

    protected renderKeyFields(): SlottedTemplateResult {
        return html`
            <ak-text-input
                label=${msg("Public Key")}
                required
                name="publicKey"
                type="text"
                value="${ifDefined(this.instance?.publicKey || "")}"
                autocomplete="off"
                input-hint="code"
                placeholder=${msg("Paste your CAPTCHA public key...")}
                help=${msg("The public key is used by authentik to render the CAPTCHA widget.", {
                    id: "captcha.public-key.description",
                    desc: "Description for CAPTCHA public key field.",
                })}
            >
            </ak-text-input>

            <ak-secret-text-input
                name="privateKey"
                label=${msg("Secret Key")}
                input-hint="code"
                ?required=${!this.instance}
                ?revealed=${!this.instance}
                placeholder=${msg("Paste your CAPTCHA secret key...")}
                help=${msg(
                    "The secret key allows communication between authentik and the CAPTCHA provider to validate user responses.",
                    {
                        id: "captcha.secret-key.description",
                        desc: "Description for CAPTCHA secret key field.",
                    },
                )}
            ></ak-secret-text-input>
        `;
    }

    protected renderScoreConfiguration(): SlottedTemplateResult {
        if (!this.#currentPreset.supportsScore) {
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

        const formValues = pluckFormValues(this.instance, this.#currentPreset);

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

    protected renderAdvancedSettings(): SlottedTemplateResult {
        const formValues = pluckFormValues(this.instance, this.#currentPreset);

        return html`<ak-form-group label="${msg("Advanced Settings")}">
            <div class="pf-c-form">
                <ak-text-input
                    label=${msg("JavaScript URL")}
                    name="jsUrl"
                    type="url"
                    value="${ifDefined(formValues.jsUrl)}"
                    required
                    help=${msg(
                        "URL to fetch the CAPTCHA JavaScript library from. Automatically set based on provider selection but can be customized.",
                    )}
                ></ak-text-input>
                <ak-text-input
                    label=${msg("API Verification URL")}
                    name="apiUrl"
                    type="url"
                    value="${ifDefined(formValues.apiUrl)}"
                    required
                    help=${msg(
                        "URL used to validate CAPTCHA response on the backend. Automatically set based on provider selection but can be customized.",
                    )}
                ></ak-text-input>
            </div>
        </ak-form-group>`;
    }

    protected override renderForm(): SlottedTemplateResult {
        const formValues = pluckFormValues(this.instance, this.#currentPreset);

        return html`
            <header>
                ${msg(
                    "This stage checks the user's current session against a CAPTCHA service to prevent automated abuse.",
                )}
            </header>
            <ak-text-input
                label=${msg("Stage Name")}
                required
                name="name"
                value="${this.instance?.name || "my-captcha-stage"}"
                placeholder=${msg("Type a stage name...")}
                autocomplete="off"
                help=${msg("The unique name used internally to identify the stage.")}
            ></ak-text-input>

            <ak-form-group open label="${msg("CAPTCHA Provider")}">
                <div class="pf-c-form">
                    ${this.renderProviderSelector()} ${this.renderKeyFields()}
                    <ak-switch-input
                        name="interactive"
                        label=${msg("Interactive")}
                        ?checked=${formValues.interactive}
                        help=${msg(
                            "Enable this if the CAPTCHA requires user interaction (clicking checkbox, solving puzzles, etc.). Required for reCAPTCHA v2, hCaptcha interactive mode, and Cloudflare Turnstile.",
                        )}
                    ></ak-switch-input>
                </div>
            </ak-form-group>

            ${this.renderScoreConfiguration()} ${this.renderAdvancedSettings()}
        `;
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-captcha-form": CaptchaStageForm;
    }
}

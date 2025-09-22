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
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-stage-captcha-form")
export class CaptchaStageForm extends BaseStageForm<CaptchaStage> {
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

    renderForm(): TemplateResult {
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
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Public key, acquired from https://www.google.com/recaptcha/intro/v3.html.",
                            )}
                        </p>
                    </ak-form-element-horizontal>

                    <ak-secret-text-input
                        name="privateKey"
                        label=${msg("Private Key")}
                        input-hint="code"
                        ?required=${!this.instance}
                        ?revealed=${!this.instance}
                        help=${msg(
                            "Private key, acquired from https://www.google.com/recaptcha/intro/v3.html.",
                        )}
                    ></ak-secret-text-input>

                    <ak-switch-input
                        name="interactive"
                        label=${msg("Interactive")}
                        ?checked="${this.instance?.interactive}"
                        help=${msg(
                            "Enable this flag if the configured captcha requires User-interaction. Required for reCAPTCHA v2, hCaptcha and Cloudflare Turnstile.",
                        )}
                    >
                    </ak-switch-input>
                    <ak-number-input
                        label=${msg("Score minimum threshold")}
                        required
                        name="scoreMinThreshold"
                        value="${ifDefined(this.instance?.scoreMinThreshold || 0.5)}"
                        help=${msg("Minimum required score to allow continuing")}
                    ></ak-number-input>
                    <ak-number-input
                        label=${msg("Score maximum threshold")}
                        required
                        name="scoreMaxThreshold"
                        value="${ifDefined(this.instance?.scoreMaxThreshold || -1)}"
                        help=${msg("Maximum allowed score to allow continuing")}
                    ></ak-number-input>
                    <ak-switch-input
                        ?checked=${!!(this.instance?.errorOnInvalidScore ?? true)}
                        name="errorOnInvalidScore"
                        label=${msg("Error on invalid score")}
                        help=${msg(
                            "When enabled and the resultant score is outside the threshold, the user will not be able to continue. When disabled, the user will be able to continue and the score can be used in policies to customize further stages.",
                        )}
                    ></ak-switch-input>
                </div>
            </ak-form-group>
            <ak-form-group label="${msg("Advanced settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal label=${msg("JS URL")} required name="jsUrl">
                        <input
                            type="url"
                            value="${ifDefined(
                                this.instance?.jsUrl ||
                                    "https://www.recaptcha.net/recaptcha/api.js",
                            )}"
                            class="pf-c-form-control pf-m-monospace"
                            autocomplete="off"
                            spellcheck="false"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "URL to fetch JavaScript from, defaults to recaptcha. Can be replaced with any compatible alternative.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("API URL")} required name="apiUrl">
                        <input
                            type="url"
                            value="${ifDefined(
                                this.instance?.apiUrl ||
                                    "https://www.recaptcha.net/recaptcha/api/siteverify",
                            )}"
                            class="pf-c-form-control pf-m-monospace"
                            autocomplete="off"
                            spellcheck="false"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "URL used to validate captcha response, defaults to recaptcha. Can be replaced with any compatible alternative.",
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

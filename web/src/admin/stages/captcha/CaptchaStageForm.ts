import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { CaptchaStage, CaptchaStageRequest, StagesApi } from "@goauthentik/api";

@customElement("ak-stage-captcha-form")
export class CaptchaStageForm extends ModelForm<CaptchaStage, string> {
    loadInstance(pk: string): Promise<CaptchaStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesCaptchaRetrieve({
            stageUuid: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated stage.`;
        } else {
            return t`Successfully created stage.`;
        }
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

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <div class="form-help-text">
                ${t`This stage checks the user's current session against the Google reCaptcha (or compatible) service.`}
            </div>
            <ak-form-element-horizontal label=${t`Name`} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name || "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header"> ${t`Stage-specific settings`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${t`Public Key`}
                        ?required=${true}
                        name="publicKey"
                    >
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.publicKey || "")}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`Public key, acquired from https://www.google.com/recaptcha/intro/v3.html.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Private Key`}
                        ?required=${true}
                        ?writeOnly=${this.instance !== undefined}
                        name="privateKey"
                    >
                        <input type="text" value="" class="pf-c-form-control" required />
                        <p class="pf-c-form__helper-text">
                            ${t`Private key, acquired from https://www.google.com/recaptcha/intro/v3.html.`}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group>
                <span slot="header"> ${t`Advanced settings`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal label=${t`JS URL`} ?required=${true} name="jsUrl">
                        <input
                            type="text"
                            value="${ifDefined(
                                this.instance?.jsUrl ||
                                    "https://www.recaptcha.net/recaptcha/api.js",
                            )}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`URL to fetch JavaScript from, defaults to recaptcha. Can be replaced with any compatible alternative.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${t`API URL`} ?required=${true} name="apiUrl">
                        <input
                            type="text"
                            value="${ifDefined(
                                this.instance?.apiUrl ||
                                    "https://www.recaptcha.net/recaptcha/api/siteverify",
                            )}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`URL used to validate captcha response, defaults to recaptcha. Can be replaced with any compatible alternative.`}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}

import { CaptchaStage, StagesApi } from "authentik-api";
import { gettext } from "django";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { Form } from "../../../elements/forms/Form";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../../elements/forms/HorizontalFormElement";
import "../../../elements/forms/FormGroup";

@customElement("ak-stage-captcha-form")
export class CaptchaStageForm extends Form<CaptchaStage> {

    set stageUUID(value: string) {
        new StagesApi(DEFAULT_CONFIG).stagesCaptchaRead({
            stageUuid: value,
        }).then(stage => {
            this.stage = stage;
        });
    }

    @property({attribute: false})
    stage?: CaptchaStage;

    getSuccessMessage(): string {
        if (this.stage) {
            return gettext("Successfully updated stage.");
        } else {
            return gettext("Successfully created stage.");
        }
    }

    send = (data: CaptchaStage): Promise<CaptchaStage> => {
        if (this.stage) {
            return new StagesApi(DEFAULT_CONFIG).stagesCaptchaUpdate({
                stageUuid: this.stage.pk || "",
                data: data
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesCaptchaCreate({
                data: data
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                label=${gettext("Name")}
                ?required=${true}
                name="name">
                <input type="text" value="${ifDefined(this.stage?.name || "")}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header">
                    ${gettext("Stage-specific settings")}
                </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${gettext("Public Key")}
                        name="publicKey">
                        <input type="text" value="${ifDefined(this.stage?.publicKey || "")}" class="pf-c-form-control">
                        <p class="pf-c-form__helper-text">${gettext("Public key, acquired from https://www.google.com/recaptcha/intro/v3.html.")}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${gettext("Public Key")}
                        name="privateKey">
                        <input type="text" value="${ifDefined(this.stage?.privateKey || "")}" class="pf-c-form-control">
                        <p class="pf-c-form__helper-text">${gettext("Public key, acquired from https://www.google.com/recaptcha/intro/v3.html.")}</p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }

}

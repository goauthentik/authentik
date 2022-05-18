import { t } from "@lingui/macro";

import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { CSSResult, LitElement, TemplateResult, html } from "lit";
import { property } from "lit/decorators.js";

import AKGlobal from "../../authentik.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { StagesApi, TypeCreate } from "@goauthentik/api";

import { DEFAULT_CONFIG } from "../../api/Config";
import "../../elements/forms/ProxyForm";
import "../../elements/wizard/FormWizardPage";
import "../../elements/wizard/Wizard";
import { WizardPage } from "../../elements/wizard/WizardPage";
import "./authenticator_duo/AuthenticatorDuoStageForm.ts";
import "./authenticator_sms/AuthenticatorSMSStageForm.ts";
import "./authenticator_static/AuthenticatorStaticStageForm.ts";
import "./authenticator_totp/AuthenticatorTOTPStageForm.ts";
import "./authenticator_validate/AuthenticatorValidateStageForm.ts";
import "./authenticator_webauthn/AuthenticateWebAuthnStageForm.ts";
import "./captcha/CaptchaStageForm.ts";
import "./consent/ConsentStageForm.ts";
import "./deny/DenyStageForm.ts";
import "./dummy/DummyStageForm.ts";
import "./email/EmailStageForm.ts";
import "./identification/IdentificationStageForm.ts";
import "./invitation/InvitationStageForm.ts";
import "./password/PasswordStageForm.ts";
import "./prompt/PromptStageForm.ts";
import "./user_delete/UserDeleteStageForm.ts";
import "./user_login/UserLoginStageForm.ts";
import "./user_logout/UserLogoutStageForm.ts";
import "./user_write/UserWriteStageForm.ts";

@customElement("ak-stage-wizard-initial")
export class InitialStageWizardPage extends WizardPage {
    @property({ attribute: false })
    stageTypes: TypeCreate[] = [];

    static get styles(): CSSResult[] {
        return [PFBase, PFForm, PFButton, AKGlobal, PFRadio];
    }

    render(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            ${this.stageTypes.map((type) => {
                return html`<div class="pf-c-radio">
                    <input
                        class="pf-c-radio__input"
                        type="radio"
                        name="type"
                        id=${`${type.component}-${type.modelName}`}
                        @change=${() => {
                            this.host.setSteps(
                                "initial",
                                `type-${type.component}-${type.modelName}`,
                            );
                            this._isValid = true;
                        }}
                    />
                    <label class="pf-c-radio__label" for=${`${type.component}-${type.modelName}`}
                        >${type.name}</label
                    >
                    <span class="pf-c-radio__description">${type.description}</span>
                </div>`;
            })}
        </form>`;
    }
}

@customElement("ak-stage-wizard")
export class StageWizard extends LitElement {
    static get styles(): CSSResult[] {
        return [PFBase, PFButton, AKGlobal, PFRadio];
    }

    @property()
    createText = t`Create`;

    @property({ attribute: false })
    stageTypes: TypeCreate[] = [];

    firstUpdated(): void {
        new StagesApi(DEFAULT_CONFIG).stagesAllTypesList().then((types) => {
            this.stageTypes = types;
        });
    }

    render(): TemplateResult {
        return html`
            <ak-wizard
                .steps=${["initial"]}
                header=${t`New stage`}
                description=${t`Create a new stage.`}
            >
                <ak-stage-wizard-initial
                    slot="initial"
                    .sidebarLabel=${() => t`Select type`}
                    .stageTypes=${this.stageTypes}
                >
                </ak-stage-wizard-initial>
                ${this.stageTypes.map((type) => {
                    return html`
                        <ak-wizard-page-form
                            slot=${`type-${type.component}-${type.modelName}`}
                            .sidebarLabel=${() => t`Create ${type.name}`}
                        >
                            <ak-proxy-form type=${type.component}></ak-proxy-form>
                        </ak-wizard-page-form>
                    `;
                })}
                <button slot="trigger" class="pf-c-button pf-m-primary">${this.createText}</button>
            </ak-wizard>
        `;
    }
}

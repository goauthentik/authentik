import { StageBindingForm } from "@goauthentik/admin/flows/StageBindingForm.js";
import "@goauthentik/admin/stages/authenticator_duo/AuthenticatorDuoStageForm.js";
import "@goauthentik/admin/stages/authenticator_sms/AuthenticatorSMSStageForm.js";
import "@goauthentik/admin/stages/authenticator_static/AuthenticatorStaticStageForm.js";
import "@goauthentik/admin/stages/authenticator_totp/AuthenticatorTOTPStageForm.js";
import "@goauthentik/admin/stages/authenticator_validate/AuthenticatorValidateStageForm.js";
import "@goauthentik/admin/stages/authenticator_webauthn/AuthenticateWebAuthnStageForm.js";
import "@goauthentik/admin/stages/captcha/CaptchaStageForm.js";
import "@goauthentik/admin/stages/consent/ConsentStageForm.js";
import "@goauthentik/admin/stages/deny/DenyStageForm.js";
import "@goauthentik/admin/stages/dummy/DummyStageForm.js";
import "@goauthentik/admin/stages/email/EmailStageForm.js";
import "@goauthentik/admin/stages/identification/IdentificationStageForm.js";
import "@goauthentik/admin/stages/invitation/InvitationStageForm.js";
import "@goauthentik/admin/stages/password/PasswordStageForm.js";
import "@goauthentik/admin/stages/prompt/PromptStageForm.js";
import "@goauthentik/admin/stages/user_delete/UserDeleteStageForm.js";
import "@goauthentik/admin/stages/user_login/UserLoginStageForm.js";
import "@goauthentik/admin/stages/user_logout/UserLogoutStageForm.js";
import "@goauthentik/admin/stages/user_write/UserWriteStageForm.js";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config.js";
import { AKElement } from "@goauthentik/elements/Base.js";
import "@goauthentik/elements/forms/ProxyForm.js";
import "@goauthentik/elements/wizard/FormWizardPage.js";
import { FormWizardPage } from "@goauthentik/elements/wizard/FormWizardPage.js";
import "@goauthentik/elements/wizard/Wizard.js";
import { WizardPage } from "@goauthentik/elements/wizard/WizardPage.js";

import { msg, str } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { CSSResult, TemplateResult, html } from "lit";
import { property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { FlowStageBinding, Stage, StagesApi, TypeCreate } from "@goauthentik/api";

@customElement("ak-stage-wizard-initial")
export class InitialStageWizardPage extends WizardPage {
    @property({ attribute: false })
    stageTypes: TypeCreate[] = [];
    sidebarLabel = () => msg("Select type");

    static get styles(): CSSResult[] {
        return [PFBase, PFForm, PFButton, PFRadio];
    }

    activeCallback: () => Promise<void> = async () => {
        this.host.isValid = false;
        this.shadowRoot
            ?.querySelectorAll<HTMLInputElement>("input[type=radio]")
            .forEach((radio) => {
                if (radio.checked) {
                    radio.dispatchEvent(new CustomEvent("change"));
                }
            });
    };

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
                            const idx = this.host.steps.indexOf("initial") + 1;
                            // Exclude all current steps starting with type-,
                            // this happens when the user selects a type and then goes back
                            this.host.steps = this.host.steps.filter(
                                (step) => !step.startsWith("type-"),
                            );
                            this.host.steps.splice(
                                idx,
                                0,
                                `type-${type.component}-${type.modelName}`,
                            );
                            this.host.isValid = true;
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
export class StageWizard extends AKElement {
    static get styles(): CSSResult[] {
        return [PFBase, PFButton, PFRadio];
    }

    @property()
    createText = msg("Create");

    @property({ type: Boolean })
    showBindingPage = false;

    @property()
    bindingTarget?: string;

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
                .steps=${this.showBindingPage ? ["initial", "create-binding"] : ["initial"]}
                header=${msg("New stage")}
                description=${msg("Create a new stage.")}
            >
                <ak-stage-wizard-initial slot="initial" .stageTypes=${this.stageTypes}>
                </ak-stage-wizard-initial>
                ${this.stageTypes.map((type) => {
                    return html`
                        <ak-wizard-page-form
                            slot=${`type-${type.component}-${type.modelName}`}
                            .sidebarLabel=${() => msg(str`Create ${type.name}`)}
                        >
                            <ak-proxy-form type=${type.component}></ak-proxy-form>
                        </ak-wizard-page-form>
                    `;
                })}
                ${this.showBindingPage
                    ? html`<ak-wizard-page-form
                          slot="create-binding"
                          .sidebarLabel=${() => msg("Create Binding")}
                          .activePageCallback=${async (context: FormWizardPage) => {
                              const createSlot = context.host.steps[1];
                              const bindingForm =
                                  context.querySelector<StageBindingForm>("ak-stage-binding-form");
                              if (!bindingForm) return;
                              bindingForm.instance = {
                                  stage: (context.host.state[createSlot] as Stage).pk,
                              } as FlowStageBinding;
                          }}
                      >
                          <ak-stage-binding-form
                              .targetPk=${this.bindingTarget}
                          ></ak-stage-binding-form>
                      </ak-wizard-page-form>`
                    : html``}
                <button slot="trigger" class="pf-c-button pf-m-primary">${this.createText}</button>
            </ak-wizard>
        `;
    }
}

import "#admin/common/ak-license-notice";
import "#admin/stages/authenticator_duo/AuthenticatorDuoStageForm";
import "#admin/stages/authenticator_email/AuthenticatorEmailStageForm";
import "#admin/stages/authenticator_sms/AuthenticatorSMSStageForm";
import "#admin/stages/authenticator_static/AuthenticatorStaticStageForm";
import "#admin/stages/authenticator_totp/AuthenticatorTOTPStageForm";
import "#admin/stages/authenticator_validate/AuthenticatorValidateStageForm";
import "#admin/stages/authenticator_webauthn/AuthenticatorWebAuthnStageForm";
import "#admin/stages/captcha/CaptchaStageForm";
import "#admin/stages/consent/ConsentStageForm";
import "#admin/stages/deny/DenyStageForm";
import "#admin/stages/dummy/DummyStageForm";
import "#admin/stages/email/EmailStageForm";
import "#admin/stages/identification/IdentificationStageForm";
import "#admin/stages/invitation/InvitationStageForm";
import "#admin/stages/mtls/MTLSStageForm";
import "#admin/stages/endpoint/EndpointStageForm";
import "#admin/stages/password/PasswordStageForm";
import "#admin/stages/prompt/PromptStageForm";
import "#admin/stages/redirect/RedirectStageForm";
import "#admin/stages/source/SourceStageForm";
import "#admin/stages/user_delete/UserDeleteStageForm";
import "#admin/stages/user_login/UserLoginStageForm";
import "#admin/stages/user_logout/UserLogoutStageForm";
import "#admin/stages/user_write/UserWriteStageForm";
import "#elements/wizard/FormWizardPage";
import "#elements/wizard/TypeCreateWizardPage";
import "#elements/wizard/Wizard";

import { DEFAULT_CONFIG } from "#common/api/config";

import { AKElement } from "#elements/Base";
import { StrictUnsafe } from "#elements/utils/unsafe";
import { FormWizardPage } from "#elements/wizard/FormWizardPage";
import { Wizard } from "#elements/wizard/Wizard";

import { StageBindingForm } from "#admin/flows/StageBindingForm";

import { FlowStageBinding, Stage, StagesApi, TypeCreate } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { CSSResult, html, nothing, TemplateResult } from "lit";
import { property, query } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";

@customElement("ak-stage-wizard")
export class StageWizard extends AKElement {
    static styles: CSSResult[] = [PFButton];

    @property()
    createText = msg("Create");

    @property({ type: Boolean })
    showBindingPage = false;

    @property()
    bindingTarget?: string;

    @property({ attribute: false })
    stageTypes: TypeCreate[] = [];

    @query("ak-wizard")
    wizard?: Wizard;

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
                <ak-wizard-page-type-create
                    slot="initial"
                    .types=${this.stageTypes}
                    @select=${(ev: CustomEvent<TypeCreate>) => {
                        if (!this.wizard) return;
                        const idx = this.wizard.steps.indexOf("initial") + 1;
                        // Exclude all current steps starting with type-,
                        // this happens when the user selects a type and then goes back
                        this.wizard.steps = this.wizard.steps.filter(
                            (step) => !step.startsWith("type-"),
                        );
                        this.wizard.steps.splice(
                            idx,
                            0,
                            `type-${ev.detail.component}-${ev.detail.modelName}`,
                        );
                        this.wizard.isValid = true;
                    }}
                >
                </ak-wizard-page-type-create>
                ${this.stageTypes.map((type) => {
                    return html`
                        <ak-wizard-page-form
                            slot=${`type-${type.component}-${type.modelName}`}
                            label=${msg(str`Create ${type.name}`)}
                        >
                            ${StrictUnsafe(type.component)}
                        </ak-wizard-page-form>
                    `;
                })}
                ${this.showBindingPage
                    ? html`<ak-wizard-page-form
                          slot="create-binding"
                          label=${msg("Create Binding")}
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
                    : nothing}
                <button slot="trigger" class="pf-c-button pf-m-primary">${this.createText}</button>
            </ak-wizard>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-wizard": StageWizard;
    }
}

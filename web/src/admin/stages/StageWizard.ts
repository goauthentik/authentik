import "@goauthentik/admin/common/ak-license-notice";
import { StageBindingForm } from "@goauthentik/admin/flows/StageBindingForm";
import "@goauthentik/admin/stages/authenticator_duo/AuthenticatorDuoStageForm";
import "@goauthentik/admin/stages/authenticator_email/AuthenticatorEmailStageForm";
import "@goauthentik/admin/stages/authenticator_sms/AuthenticatorSMSStageForm";
import "@goauthentik/admin/stages/authenticator_static/AuthenticatorStaticStageForm";
import "@goauthentik/admin/stages/authenticator_totp/AuthenticatorTOTPStageForm";
import "@goauthentik/admin/stages/authenticator_validate/AuthenticatorValidateStageForm";
import "@goauthentik/admin/stages/authenticator_webauthn/AuthenticatorWebAuthnStageForm";
import "@goauthentik/admin/stages/captcha/CaptchaStageForm";
import "@goauthentik/admin/stages/consent/ConsentStageForm";
import "@goauthentik/admin/stages/deny/DenyStageForm";
import "@goauthentik/admin/stages/dummy/DummyStageForm";
import "@goauthentik/admin/stages/email/EmailStageForm";
import "@goauthentik/admin/stages/identification/IdentificationStageForm";
import "@goauthentik/admin/stages/invitation/InvitationStageForm";
import "@goauthentik/admin/stages/password/PasswordStageForm";
import "@goauthentik/admin/stages/prompt/PromptStageForm";
import "@goauthentik/admin/stages/redirect/RedirectStageForm";
import "@goauthentik/admin/stages/source/SourceStageForm";
import "@goauthentik/admin/stages/user_delete/UserDeleteStageForm";
import "@goauthentik/admin/stages/user_login/UserLoginStageForm";
import "@goauthentik/admin/stages/user_logout/UserLogoutStageForm";
import "@goauthentik/admin/stages/user_write/UserWriteStageForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/forms/ProxyForm";
import "@goauthentik/elements/wizard/FormWizardPage";
import { FormWizardPage } from "@goauthentik/elements/wizard/FormWizardPage";
import "@goauthentik/elements/wizard/TypeCreateWizardPage";
import "@goauthentik/elements/wizard/Wizard";
import { Wizard } from "@goauthentik/elements/wizard/Wizard";

import { msg, str } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { CSSResult, TemplateResult, html } from "lit";
import { property, query } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { FlowStageBinding, Stage, StagesApi, TypeCreate } from "@goauthentik/api";

@customElement("ak-stage-wizard")
export class StageWizard extends AKElement {
    static get styles(): CSSResult[] {
        return [PFBase, PFButton];
    }

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

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-wizard": StageWizard;
    }
}

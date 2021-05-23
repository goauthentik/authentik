import { t } from "@lingui/macro";
import { CSSResult, customElement, html, property, TemplateResult } from "lit-element";
import { WithUserInfoChallenge } from "../../../api/Flows";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import AKGlobal from "../../../authentik.css";
import { BaseStage } from "../base";
import "../../../elements/forms/FormElement";
import "../../../elements/EmptyState";
import "../../FormStatic";
import { FlowURLManager } from "../../../api/legacy";
import { StagesApi } from "authentik-api";
import { DEFAULT_CONFIG } from "../../../api/Config";

export interface AuthenticatorDuoChallenge extends WithUserInfoChallenge {
    activation_barcode: string;
    activation_code: string;
    stage_uuid: string;
}

@customElement("ak-stage-authenticator-duo")
export class AuthenticatorDuoStage extends BaseStage {

    @property({ attribute: false })
    challenge?: AuthenticatorDuoChallenge;

    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFForm, PFFormControl, PFTitle, PFButton, AKGlobal];
    }

    firstUpdated(): void {
        const i = setInterval(() => {
            this.checkEnrollStatus().then(() => {
                clearInterval(i);
            });
        }, 3000);
    }

    checkEnrollStatus(): Promise<void> {
        return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorDuoEnrollmentStatusCreate({
            stageUuid: this.challenge?.stage_uuid || "",
        }).then(r => {
            this.host?.submit({});
        }).catch(e => {
        });
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-empty-state
                ?loading="${true}"
                header=${t`Loading`}>
            </ak-empty-state>`;
        }
        return html`<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">
                    ${this.challenge.title}
                </h1>
            </header>
            <div class="pf-c-login__main-body">
                <form class="pf-c-form" @submit=${(e: Event) => { this.submitForm(e); }}>
                    <ak-form-static
                        class="pf-c-form__group"
                        userAvatar="${this.challenge.pending_user_avatar}"
                        user=${this.challenge.pending_user}>
                        <div slot="link">
                            <a href="${FlowURLManager.cancel()}">${t`Not you?`}</a>
                        </div>
                    </ak-form-static>
                    <img src=${this.challenge.activation_barcode} />
                    <p>
                        ${t`Alternatively, if your current device has Duo installed, click on this link:`}
                    </p>
                    <a href=${this.challenge.activation_code}>${t`Duo activation`}</a>

                    <div class="pf-c-form__group pf-m-action">
                        <button type="button" class="pf-c-button pf-m-primary pf-m-block" @click=${() => {
                            this.checkEnrollStatus();
                        }}>
                            ${t`Check status`}
                        </button>
                    </div>
                </form>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links">
                </ul>
            </footer>`;
    }

}

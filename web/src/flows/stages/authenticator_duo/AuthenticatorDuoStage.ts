import { t } from "@lingui/macro";
import { CSSResult, customElement, html, TemplateResult } from "lit-element";
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
import {
    AuthenticatorDuoChallenge,
    AuthenticatorDuoChallengeResponseRequest,
    StagesApi,
} from "authentik-api";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { ifDefined } from "lit-html/directives/if-defined";

@customElement("ak-stage-authenticator-duo")
export class AuthenticatorDuoStage extends BaseStage<
    AuthenticatorDuoChallenge,
    AuthenticatorDuoChallengeResponseRequest
> {
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
        return new StagesApi(DEFAULT_CONFIG)
            .stagesAuthenticatorDuoEnrollmentStatusCreate({
                stageUuid: this.challenge?.stageUuid || "",
            })
            .then(() => {
                this.host?.submit({});
            })
            .catch(() => {
                console.debug("authentik/flows/duo: Waiting for auth status");
            });
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-empty-state ?loading="${true}" header=${t`Loading`}> </ak-empty-state>`;
        }
        return html`<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">${this.challenge.flowInfo?.title}</h1>
            </header>
            <div class="pf-c-login__main-body">
                <form
                    class="pf-c-form"
                    @submit=${(e: Event) => {
                        this.submitForm(e);
                    }}
                >
                    <ak-form-static
                        class="pf-c-form__group"
                        userAvatar="${this.challenge.pendingUserAvatar}"
                        user=${this.challenge.pendingUser}
                    >
                        <div slot="link">
                            <a href="${ifDefined(this.challenge.flowInfo?.cancelUrl)}"
                                >${t`Not you?`}</a
                            >
                        </div>
                    </ak-form-static>
                    <img src=${this.challenge.activationBarcode} />
                    <p>
                        ${t`Alternatively, if your current device has Duo installed, click on this link:`}
                    </p>
                    <a href=${this.challenge.activationCode}>${t`Duo activation`}</a>

                    <div class="pf-c-form__group pf-m-action">
                        <button
                            type="button"
                            class="pf-c-button pf-m-primary pf-m-block"
                            @click=${() => {
                                this.checkEnrollStatus();
                            }}
                        >
                            ${t`Check status`}
                        </button>
                    </div>
                </form>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links"></ul>
            </footer>`;
    }
}

import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/EmptyState";
import "@goauthentik/elements/forms/FormElement";
import "@goauthentik/flow/FormStatic";
import { BaseStage } from "@goauthentik/flow/stages/base";

import { t } from "@lingui/macro";

import { CSSResult, TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import {
    AuthenticatorDuoChallenge,
    AuthenticatorDuoChallengeResponseRequest,
    DuoResponseEnum,
    StagesApi,
} from "@goauthentik/api";

@customElement("ak-stage-authenticator-duo")
export class AuthenticatorDuoStage extends BaseStage<
    AuthenticatorDuoChallenge,
    AuthenticatorDuoChallengeResponseRequest
> {
    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFForm, PFFormControl, PFTitle, PFButton];
    }

    firstUpdated(): void {
        const i = setInterval(() => {
            this.checkEnrollStatus().then((shouldStop) => {
                if (shouldStop) {
                    clearInterval(i);
                }
            });
        }, 3000);
    }

    async checkEnrollStatus(): Promise<boolean> {
        const status = await new StagesApi(
            DEFAULT_CONFIG,
        ).stagesAuthenticatorDuoEnrollmentStatusCreate({
            stageUuid: this.challenge?.stageUuid || "",
        });
        console.debug(
            `authentik/stages/authenticator_duo: Enrollment status: ${status.duoResponse}`,
        );
        switch (status.duoResponse) {
            case DuoResponseEnum.Success:
                this.host?.submit({});
                return true;
            case DuoResponseEnum.Waiting:
                break;
        }
        return false;
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
                    <img src=${this.challenge.activationBarcode} alt=${t`Duo activation QR code`} />
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

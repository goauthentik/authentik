import "#flow/FormStatic";
import "#flow/components/ak-flow-card";

import { DEFAULT_CONFIG } from "#common/api/config";

import { BaseStage } from "#flow/stages/base";

import {
    AuthenticatorDuoChallenge,
    AuthenticatorDuoChallengeResponseRequest,
    DuoResponseEnum,
    StagesApi,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, PropertyValues, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-stage-authenticator-duo")
export class AuthenticatorDuoStage extends BaseStage<
    AuthenticatorDuoChallenge,
    AuthenticatorDuoChallengeResponseRequest
> {
    static styles: CSSResult[] = [PFBase, PFLogin, PFForm, PFFormControl, PFTitle, PFButton];

    updated(changedProperties: PropertyValues<this>) {
        if (changedProperties.has("challenge") && this.challenge !== undefined) {
            const i = setInterval(() => {
                this.checkEnrollStatus().then((shouldStop) => {
                    if (shouldStop) {
                        clearInterval(i);
                    }
                });
            }, 3000);
        }
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
        return html`<ak-flow-card .challenge=${this.challenge}>
            <form class="pf-c-form" @submit=${this.submitForm}>
                <ak-form-static
                    class="pf-c-form__group"
                    userAvatar="${this.challenge.pendingUserAvatar}"
                    user=${this.challenge.pendingUser}
                >
                    <div slot="link">
                        <a href="${ifDefined(this.challenge.flowInfo?.cancelUrl)}"
                            >${msg("Not you?")}</a
                        >
                    </div>
                </ak-form-static>
                <img src=${this.challenge.activationBarcode} alt=${msg("Duo activation QR code")} />
                <p>
                    ${msg(
                        "Alternatively, if your current device has Duo installed, click on this link:",
                    )}
                </p>
                <a href=${this.challenge.activationCode}>${msg("Duo activation")}</a>

                <div class="pf-c-form__group pf-m-action">
                    <button
                        type="button"
                        class="pf-c-button pf-m-primary pf-m-block"
                        @click=${() => {
                            this.checkEnrollStatus();
                        }}
                    >
                        ${msg("Check status")}
                    </button>
                </div>
            </form>
        </ak-flow-card>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-authenticator-duo": AuthenticatorDuoStage;
    }
}

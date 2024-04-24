import "@goauthentik/elements/EmptyState";
import "@goauthentik/elements/forms/FormElement";
import { BaseDeviceStage } from "@goauthentik/flow/stages/authenticator_validate/base";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import {
    AuthenticatorValidationChallenge,
    AuthenticatorValidationChallengeResponseRequest,
    DeviceChallenge,
} from "@goauthentik/api";

@customElement("ak-stage-authenticator-validate-duo")
export class AuthenticatorValidateStageWebDuo extends BaseDeviceStage<
    AuthenticatorValidationChallenge,
    AuthenticatorValidationChallengeResponseRequest
> {
    @property({ attribute: false })
    deviceChallenge?: DeviceChallenge;

    @property({ type: Boolean })
    showBackButton = false;

    @state()
    authenticating = false;

    firstUpdated(): void {
        this.authenticating = true;
        this.host
            ?.submit(
                {
                    duo: this.deviceChallenge?.deviceUid,
                },
                { invisible: true },
            )
            .then(() => {
                this.authenticating = false;
            })
            .catch(() => {
                this.authenticating = false;
            });
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-empty-state ?loading="${true}" header=${msg("Loading")}>
            </ak-empty-state>`;
        }
        const errors = this.challenge.responseErrors?.duo || [];
        const errorMessage = errors.map((err) => err.string);
        return html`<div class="pf-c-login__main-body">
            <form
                class="pf-c-form"
                @submit=${(e: Event) => {
                    this.submitForm(e);
                }}
            >
                ${this.renderUserInfo()}
                <ak-empty-state
                    ?loading="${this.authenticating}"
                    header=${this.authenticating
                        ? msg("Sending Duo push notification...")
                        : errorMessage.join(", ") || msg("Failed to authenticate")}
                    icon="fas fa-times"
                >
                </ak-empty-state>
                <div class="pf-c-form__group pf-m-action">${this.renderReturnToDevicePicker()}</div>
            </form>
        </div>`;
    }
}

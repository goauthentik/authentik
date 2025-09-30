import "#elements/EmptyState";

import { BaseDeviceStage } from "#flow/stages/authenticator_validate/base";

import {
    AuthenticatorValidationChallenge,
    AuthenticatorValidationChallengeResponseRequest,
    DeviceChallenge,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing, PropertyValues, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

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

    updated(changedProperties: PropertyValues<this>) {
        if (changedProperties.has("challenge") && this.challenge !== undefined) {
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
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-empty-state loading> </ak-empty-state>`;
        }
        const errors = this.challenge.responseErrors?.duo || [];
        const errorMessage = errors.map((err) => err.string);
        return html` <form class="pf-c-form" @submit=${this.submitForm}>
            ${this.renderUserInfo()}
            <ak-empty-state ?loading="${this.authenticating}" icon="fas fa-times"
                ><span
                    >${this.authenticating
                        ? msg("Sending Duo push notification...")
                        : errorMessage.join(", ") || msg("Failed to authenticate")}</span
                >
            </ak-empty-state>
            ${this.showBackButton
                ? html`<div class="pf-c-form__group">${this.renderReturnToDevicePicker()}</div>`
                : nothing}
        </form>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-authenticator-validate-duo": AuthenticatorValidateStageWebDuo;
    }
}

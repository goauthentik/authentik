import { customElement, html, property, TemplateResult } from "lit-element";
import { WithUserInfoChallenge } from "../../../api/Flows";
import { BaseStage, StageHost } from "../base";
import "./AuthenticatorValidateStageWebAuthn";

export enum DeviceClasses {
    STATIC = "static",
    TOTP = "totp",
    WEBAUTHN = "webauthn",
}

export interface DeviceChallenge {
    device_class: DeviceClasses;
    device_uid: string;
    challenge: unknown;
}

export interface AuthenticatorValidateStageChallenge extends WithUserInfoChallenge {
    device_challenges: DeviceChallenge[];
}

export interface AuthenticatorValidateStageChallengeResponse {
    response: DeviceChallenge;
}

@customElement("ak-stage-authenticator-validate")
export class AuthenticatorValidateStage extends BaseStage implements StageHost {

    @property({ attribute: false })
    challenge?: AuthenticatorValidateStageChallenge;

    @property({attribute: false})
    selectedDeviceChallenge?: DeviceChallenge;

    renderDeviceChallenge(): TemplateResult {
        if (!this.selectedDeviceChallenge) {
            return html``;
        }
        switch (this.selectedDeviceChallenge?.device_class) {
        case DeviceClasses.STATIC:
        case DeviceClasses.TOTP:
            // TODO: Create input for code
            return html``;
        case DeviceClasses.WEBAUTHN:
            return html`<ak-stage-authenticator-validate-webauthn
                .host=${this}
                .challenge=${this.challenge}
                .deviceChallenge=${this.selectedDeviceChallenge}>
            </ak-stage-authenticator-validate-webauthn>`;
        }
    }

    submit(formData?: FormData): Promise<void> {
        return this.host?.submit(formData) || Promise.resolve();
    }

    render(): TemplateResult {
        // User only has a single device class, so we don't show a picker
        if (this.challenge?.device_challenges.length === 1) {
            this.selectedDeviceChallenge = this.challenge.device_challenges[0];
        }
        if (this.selectedDeviceChallenge) {
            return this.renderDeviceChallenge();
        }
        // TODO: Create picker between challenges
        return html`ak-stage-authenticator-validate`;
    }

}

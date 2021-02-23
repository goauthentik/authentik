import { customElement, html, property, TemplateResult } from "lit-element";
import { WithUserInfoChallenge } from "../../../api/Flows";
import { BaseStage, StageHost } from "../base";
import "./AuthenticatorValidateStageWebAuthn";

export enum DeviceClasses {
    STATIC = "static",
    TOTP = "totp",
    WEBAUTHN = "webauthn",
}

export interface AuthenticatorValidateStageChallenge extends WithUserInfoChallenge {
    users_device_classes: DeviceClasses[];
    class_challenges: { [key in DeviceClasses]: unknown };
}

export interface AuthenticatorValidateStageChallengeResponse {
    device_challenges: { [key in DeviceClasses]: unknown}  ;
}

@customElement("ak-stage-authenticator-validate")
export class AuthenticatorValidateStage extends BaseStage implements StageHost {

    @property({ attribute: false })
    challenge?: AuthenticatorValidateStageChallenge;

    renderDeviceClass(deviceClass: DeviceClasses): TemplateResult {
        switch (deviceClass) {
        case DeviceClasses.STATIC:
        case DeviceClasses.TOTP:
            return html``;
        case DeviceClasses.WEBAUTHN:
            return html`<ak-stage-authenticator-validate-webauthn .host=${this} .challenge=${this.challenge}></ak-stage-authenticator-validate-webauthn>`;
        }
    }

    submit(formData?: FormData): Promise<void> {
        return this.host?.submit(formData) || Promise.resolve();
    }

    render(): TemplateResult {
        // User only has a single device class, so we don't show a picker
        if (this.challenge?.users_device_classes.length === 1) {
            return this.renderDeviceClass(this.challenge.users_device_classes[0]);
        }
        return html`ak-stage-authenticator-validate`;
    }

}

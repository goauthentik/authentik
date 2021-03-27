import { gettext } from "django";
import { css, CSSResult, customElement, html, property, TemplateResult } from "lit-element";
import { WithUserInfoChallenge } from "../../../api/Flows";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import AKGlobal from "../../../authentik.css";
import { BaseStage, StageHost } from "../base";
import "./AuthenticatorValidateStageWebAuthn";
import "./AuthenticatorValidateStageCode";
import { PasswordManagerPrefill } from "../identification/IdentificationStage";

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
    code: string;
    webauthn: string;
}

@customElement("ak-stage-authenticator-validate")
export class AuthenticatorValidateStage extends BaseStage implements StageHost {

    @property({ attribute: false })
    challenge?: AuthenticatorValidateStageChallenge;

    @property({attribute: false})
    selectedDeviceChallenge?: DeviceChallenge;

    submit<T>(formData?: T): Promise<void> {
        return this.host?.submit<T>(formData) || Promise.resolve();
    }

    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFForm, PFFormControl, PFTitle, PFButton, AKGlobal].concat(css`
            ul > li:not(:last-child) {
                padding-bottom: 1rem;
            }
            .authenticator-button {
                display: flex;
                align-items: center;
                width: 100%;
            }
            i {
                font-size: 1.5rem;
                padding: 1rem 0;
                width: 5rem;
            }
            .right {
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                height: 100%;
                text-align: left;
            }
            .right > * {
                height: 50%;
            }
        `);
    }

    renderDevicePickerSingle(deviceChallenge: DeviceChallenge): TemplateResult {
        switch (deviceChallenge.device_class) {
            case DeviceClasses.WEBAUTHN:
                return html`<i class="fas fa-mobile-alt"></i>
                    <div class="right">
                        <p>${gettext("Authenticator")}</p>
                        <small>${gettext("Use a security key to prove your identity.")}</small>
                    </div>`;
            case DeviceClasses.TOTP:
                // TOTP is a bit special, assuming that TOTP is allowed from the backend,
                // and we have a pre-filled value from the password manager,
                // directly set the the TOTP device Challenge as active.
                if (PasswordManagerPrefill.totp) {
                    console.debug("authentik/stages/authenticator_validate: found prefill totp code, selecting totp challenge");
                    this.selectedDeviceChallenge = deviceChallenge;
                    // Delay the update as a re-render isn't triggered from here
                    setTimeout(() => {
                        this.requestUpdate();
                    }, 100);
                }
                return html`<i class="fas fa-clock"></i>
                    <div class="right">
                        <p>${gettext("Traditional authenticator")}</p>
                        <small>${gettext("Use a code-based authenticator.")}</small>
                    </div>`;
            case DeviceClasses.STATIC:
                return html`<i class="fas fa-key"></i>
                    <div class="right">
                        <p>${gettext("Recovery keys")}</p>
                        <small>${gettext("In case you can't access any other method.")}</small>
                    </div>`;
            default:
                break;
        }
        return html``;
    }

    renderDevicePicker(): TemplateResult {
        return html`
        <ul>
            ${this.challenge?.device_challenges.map((challenges) => {
                return html`<li>
                    <button class="pf-c-button authenticator-button" type="button" @click=${() => {
                        this.selectedDeviceChallenge = challenges;
                    }}>
                        ${this.renderDevicePickerSingle(challenges)}
                    </button>
                </li>`;
            })}
        </ul>`;
    }

    renderDeviceChallenge(): TemplateResult {
        if (!this.selectedDeviceChallenge) {
            return html``;
        }
        switch (this.selectedDeviceChallenge?.device_class) {
        case DeviceClasses.STATIC:
        case DeviceClasses.TOTP:
            return html`<ak-stage-authenticator-validate-code
                .host=${this}
                .challenge=${this.challenge}
                .deviceChallenge=${this.selectedDeviceChallenge}
                .showBackButton=${(this.challenge?.device_challenges.length || []) > 1}>
            </ak-stage-authenticator-validate-code>`;
        case DeviceClasses.WEBAUTHN:
            return html`<ak-stage-authenticator-validate-webauthn
                .host=${this}
                .challenge=${this.challenge}
                .deviceChallenge=${this.selectedDeviceChallenge}
                .showBackButton=${(this.challenge?.device_challenges.length || []) > 1}>
            </ak-stage-authenticator-validate-webauthn>`;
        }
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-empty-state
                ?loading="${true}"
                header=${gettext("Loading")}>
            </ak-empty-state>`;
        }
        // User only has a single device class, so we don't show a picker
        if (this.challenge?.device_challenges.length === 1) {
            this.selectedDeviceChallenge = this.challenge.device_challenges[0];
        }
        return html`<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">
                    ${this.challenge.title}
                </h1>
                ${this.selectedDeviceChallenge ? "" : html`<p class="pf-c-login__main-header-desc">
                    ${gettext("Select an identification method.")}
                    </p>`}
            </header>
            ${this.selectedDeviceChallenge ?
                this.renderDeviceChallenge() :
                html`<div class="pf-c-login__main-body">
                    ${this.renderDevicePicker()}
                </div>
                <footer class="pf-c-login__main-footer">
                    <ul class="pf-c-login__main-footer-links">
                    </ul>
                </footer>`}`;
    }

}

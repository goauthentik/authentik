import { t } from "@lingui/macro";

import { css, CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators";

import AKGlobal from "../../../authentik.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import {
    AuthenticatorValidationChallenge,
    AuthenticatorValidationChallengeResponseRequest,
    DeviceChallenge,
    DeviceClassesEnum,
} from "@goauthentik/api";

import { BaseStage, StageHost } from "../base";
import { PasswordManagerPrefill } from "../identification/IdentificationStage";
import "./AuthenticatorValidateStageCode";
import "./AuthenticatorValidateStageDuo";
import "./AuthenticatorValidateStageWebAuthn";

@customElement("ak-stage-authenticator-validate")
export class AuthenticatorValidateStage
    extends BaseStage<
        AuthenticatorValidationChallenge,
        AuthenticatorValidationChallengeResponseRequest
    >
    implements StageHost
{
    @property({ attribute: false })
    selectedDeviceChallenge?: DeviceChallenge;

    submit(payload: AuthenticatorValidationChallengeResponseRequest): Promise<void> {
        return this.host?.submit(payload) || Promise.resolve();
    }

    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFForm, PFFormControl, PFTitle, PFButton, AKGlobal].concat(css`
            ul > li:not(:last-child) {
                padding-bottom: 1rem;
            }
            .authenticator-button {
                display: flex;
                align-items: center;
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
        switch (deviceChallenge.deviceClass) {
            case DeviceClassesEnum.Duo:
                return html`<i class="fas fa-mobile-alt"></i>
                    <div class="right">
                        <p>${t`Duo push-notifications`}</p>
                        <small
                            >${t`Receive a push notification on your phone to prove your identity.`}</small
                        >
                    </div>`;
            case DeviceClassesEnum.Webauthn:
                return html`<i class="fas fa-mobile-alt"></i>
                    <div class="right">
                        <p>${t`Authenticator`}</p>
                        <small>${t`Use a security key to prove your identity.`}</small>
                    </div>`;
            case DeviceClassesEnum.Totp:
                return html`<i class="fas fa-clock"></i>
                    <div class="right">
                        <p>${t`Traditional authenticator`}</p>
                        <small>${t`Use a code-based authenticator.`}</small>
                    </div>`;
            case DeviceClassesEnum.Static:
                return html`<i class="fas fa-key"></i>
                    <div class="right">
                        <p>${t`Recovery keys`}</p>
                        <small>${t`In case you can't access any other method.`}</small>
                    </div>`;
            case DeviceClassesEnum.Sms:
                return html`<i class="fas fa-mobile"></i>
                    <div class="right">
                        <p>${t`SMS`}</p>
                        <small>${t`Tokens sent via SMS.`}</small>
                    </div>`;
            default:
                break;
        }
        return html``;
    }

    renderDevicePicker(): TemplateResult {
        return html` <ul>
            ${this.challenge?.deviceChallenges.map((challenges) => {
                return html`<li>
                    <button
                        class="pf-c-button authenticator-button"
                        type="button"
                        @click=${() => {
                            this.selectedDeviceChallenge = challenges;
                        }}
                    >
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
        switch (this.selectedDeviceChallenge?.deviceClass) {
            case DeviceClassesEnum.Static:
            case DeviceClassesEnum.Totp:
            case DeviceClassesEnum.Sms:
                return html`<ak-stage-authenticator-validate-code
                    .host=${this}
                    .challenge=${this.challenge}
                    .deviceChallenge=${this.selectedDeviceChallenge}
                    .showBackButton=${(this.challenge?.deviceChallenges.length || []) > 1}
                >
                </ak-stage-authenticator-validate-code>`;
            case DeviceClassesEnum.Webauthn:
                return html`<ak-stage-authenticator-validate-webauthn
                    .host=${this}
                    .challenge=${this.challenge}
                    .deviceChallenge=${this.selectedDeviceChallenge}
                    .showBackButton=${(this.challenge?.deviceChallenges.length || []) > 1}
                >
                </ak-stage-authenticator-validate-webauthn>`;
            case DeviceClassesEnum.Duo:
                return html`<ak-stage-authenticator-validate-duo
                    .host=${this}
                    .challenge=${this.challenge}
                    .deviceChallenge=${this.selectedDeviceChallenge}
                    .showBackButton=${(this.challenge?.deviceChallenges.length || []) > 1}
                >
                </ak-stage-authenticator-validate-duo>`;
        }
        return html``;
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-empty-state ?loading="${true}" header=${t`Loading`}> </ak-empty-state>`;
        }
        // User only has a single device class, so we don't show a picker
        if (this.challenge?.deviceChallenges.length === 1) {
            this.selectedDeviceChallenge = this.challenge.deviceChallenges[0];
        }
        // TOTP is a bit special, assuming that TOTP is allowed from the backend,
        // and we have a pre-filled value from the password manager,
        // directly set the the TOTP device Challenge as active.
        const totpChallenge = this.challenge.deviceChallenges.find(
            (challenge) => challenge.deviceClass === DeviceClassesEnum.Totp,
        );
        if (PasswordManagerPrefill.totp && totpChallenge) {
            console.debug(
                "authentik/stages/authenticator_validate: found prefill totp code, selecting totp challenge",
            );
            this.selectedDeviceChallenge = totpChallenge;
        }
        return html`<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">${this.challenge.flowInfo?.title}</h1>
                ${this.selectedDeviceChallenge
                    ? ""
                    : html`<p class="pf-c-login__main-header-desc">
                          ${t`Select an authentication method.`}
                      </p>`}
            </header>
            ${this.selectedDeviceChallenge
                ? this.renderDeviceChallenge()
                : html`<div class="pf-c-login__main-body">${this.renderDevicePicker()}</div>
                      <footer class="pf-c-login__main-footer">
                          <ul class="pf-c-login__main-footer-links"></ul>
                      </footer>`}`;
    }
}

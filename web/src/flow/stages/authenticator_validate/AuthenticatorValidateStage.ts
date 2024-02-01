import "@goauthentik/flow/stages/authenticator_validate/AuthenticatorValidateStageCode";
import "@goauthentik/flow/stages/authenticator_validate/AuthenticatorValidateStageDuo";
import "@goauthentik/flow/stages/authenticator_validate/AuthenticatorValidateStageWebAuthn";
import { BaseStage, StageHost } from "@goauthentik/flow/stages/base";
import { PasswordManagerPrefill } from "@goauthentik/flow/stages/identification/IdentificationStage";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import {
    AuthenticatorValidationChallenge,
    AuthenticatorValidationChallengeResponseRequest,
    CurrentBrand,
    DeviceChallengeTypes,
} from "@goauthentik/api";

@customElement("ak-stage-authenticator-validate")
export class AuthenticatorValidateStage
    extends BaseStage<
        AuthenticatorValidationChallenge,
        AuthenticatorValidationChallengeResponseRequest
    >
    implements StageHost
{
    get brand(): CurrentBrand | undefined {
        return this.host.brand;
    }

    @state()
    _selectedDeviceChallenge?: DeviceChallengeTypes;

    set selectedDeviceChallenge(value: DeviceChallengeTypes | undefined) {
        const previousChallenge = this._selectedDeviceChallenge;
        this._selectedDeviceChallenge = value;
        if (value?.uid === previousChallenge?.uid) return;
        const selectionPayload: AuthenticatorValidationChallengeResponseRequest = {
            selectedChallengeUid: value?.uid || null,
            component: this.challenge.component,
        };
        this.host?.submit(selectionPayload);
    }

    get selectedDeviceChallenge(): DeviceChallengeTypes | undefined {
        return this._selectedDeviceChallenge;
    }

    get deviceChallenges(): DeviceChallengeTypes[] {
        return this.challenge.deviceChallenges as DeviceChallengeTypes[];
    }

    submit(
        payload: AuthenticatorValidationChallengeResponseRequest,
        loading: boolean = true,
    ): Promise<boolean> {
        return this.host?.submit(payload, loading) || Promise.resolve();
    }

    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFForm, PFFormControl, PFTitle, PFButton].concat(css`
            ul {
                padding-top: 1rem;
            }
            ul > li:not(:last-child) {
                padding-bottom: 1rem;
            }
            .authenticator-button {
                display: flex;
                align-items: center;
            }
            :host([theme="dark"]) .authenticator-button {
                color: var(--ak-dark-foreground) !important;
            }
            i {
                font-size: 1.5rem;
                padding: 1rem 0;
                width: 3rem;
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

    renderDevicePickerSingle(deviceChallenge: DeviceChallengeTypes): TemplateResult {
        switch (deviceChallenge.component) {
            case "ak-stage-authenticator-validate-device-duo":
                return html`<i class="fas fa-mobile-alt"></i>
                    <div class="right">
                        <p>${msg("Duo push-notifications")}</p>
                        <small>${msg("Receive a push notification on your device.")}</small>
                    </div>`;
            case "ak-stage-authenticator-validate-device-webauthn":
                return html`<i class="fas fa-mobile-alt"></i>
                    <div class="right">
                        <p>${msg("Authenticator")}</p>
                        <small>${msg("Use a security key to prove your identity.")}</small>
                    </div>`;
            case "ak-stage-authenticator-validate-device-totp":
                return html`<i class="fas fa-clock"></i>
                    <div class="right">
                        <p>${msg("Traditional authenticator")}</p>
                        <small>${msg("Use a code-based authenticator.")}</small>
                    </div>`;
            case "ak-stage-authenticator-validate-device-static":
                return html`<i class="fas fa-key"></i>
                    <div class="right">
                        <p>${msg("Recovery keys")}</p>
                        <small>${msg("In case you can't access any other method.")}</small>
                    </div>`;
            case "ak-stage-authenticator-validate-device-sms":
                return html`<i class="fas fa-mobile-alt"></i>
                    <div class="right">
                        <p>${msg("SMS")}</p>
                        <small>${msg("Tokens sent via SMS.")}</small>
                    </div>`;
            default:
                break;
        }
        return html``;
    }

    renderDevicePicker(): TemplateResult {
        return html`<ul>
            ${this.deviceChallenges.map((challenges) => {
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

    renderStagePicker(): TemplateResult {
        return html`<ul>
            ${this.challenge?.configurationStages.map((stage) => {
                return html`<li>
                    <button
                        class="pf-c-button authenticator-button"
                        type="button"
                        @click=${() => {
                            this.submit({
                                component: this.challenge.component || "",
                                selectedStage: stage.pk,
                            } as AuthenticatorValidationChallengeResponseRequest);
                        }}
                    >
                        <div class="right">
                            <p>${stage.name}</p>
                            <small>${stage.verboseName}</small>
                        </div>
                    </button>
                </li>`;
            })}
        </ul>`;
    }

    renderDeviceChallenge(): TemplateResult {
        if (!this.selectedDeviceChallenge) {
            return html``;
        }
        switch (this.selectedDeviceChallenge.component) {
            case "ak-stage-authenticator-validate-device-static":
            case "ak-stage-authenticator-validate-device-totp":
            case "ak-stage-authenticator-validate-device-sms":
                return html` <ak-stage-authenticator-validate-code
                    .host=${this}
                    .challenge=${this.challenge}
                    .deviceChallenge=${this.selectedDeviceChallenge}
                    .showBackButton=${(this.challenge?.deviceChallenges || []).length > 1}
                >
                </ak-stage-authenticator-validate-code>`;
            case "ak-stage-authenticator-validate-device-webauthn":
                return html` <ak-stage-authenticator-validate-webauthn
                    .host=${this}
                    .challenge=${this.challenge}
                    .deviceChallenge=${this.selectedDeviceChallenge}
                    .showBackButton=${(this.challenge?.deviceChallenges || []).length > 1}
                >
                </ak-stage-authenticator-validate-webauthn>`;
            case "ak-stage-authenticator-validate-device-duo":
                return html` <ak-stage-authenticator-validate-duo
                    .host=${this}
                    .challenge=${this.challenge}
                    .deviceChallenge=${this.selectedDeviceChallenge}
                    .showBackButton=${(this.challenge?.deviceChallenges || []).length > 1}
                >
                </ak-stage-authenticator-validate-duo>`;
        }
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-empty-state ?loading="${true}" header=${msg("Loading")}>
            </ak-empty-state>`;
        }
        // User only has a single device class, so we don't show a picker
        if (this.deviceChallenges.length === 1) {
            this.selectedDeviceChallenge = this.deviceChallenges[0];
        }
        // TOTP is a bit special, assuming that TOTP is allowed from the backend,
        // and we have a pre-filled value from the password manager,
        // directly set the the TOTP device Challenge as active.
        const totpChallenge = this.deviceChallenges.find(
            (challenge) => challenge.component === "ak-stage-authenticator-validate-device-totp",
        );
        if (PasswordManagerPrefill.totp && totpChallenge) {
            console.debug(
                "authentik/stages/authenticator_validate: found prefill totp code, selecting totp challenge",
            );
            this.selectedDeviceChallenge = totpChallenge;
        }
        return html`<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">${this.challenge.flowInfo?.title}</h1>
            </header>
            ${this.selectedDeviceChallenge
                ? this.renderDeviceChallenge()
                : html`<div class="pf-c-login__main-body">
                          <form class="pf-c-form">
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
                              <input
                                  name="username"
                                  autocomplete="username"
                                  type="hidden"
                                  value="${this.challenge.pendingUser}"
                              />
                              ${this.selectedDeviceChallenge
                                  ? ""
                                  : html`<p>${msg("Select an authentication method.")}</p>`}
                              ${this.challenge.configurationStages.length > 0
                                  ? this.renderStagePicker()
                                  : html``}
                          </form>
                          ${this.renderDevicePicker()}
                      </div>
                      <footer class="pf-c-login__main-footer">
                          <ul class="pf-c-login__main-footer-links"></ul>
                      </footer>`}`;
    }
}

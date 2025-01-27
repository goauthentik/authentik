import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/flow/stages/authenticator_validate/AuthenticatorValidateStageCode";
import "@goauthentik/flow/stages/authenticator_validate/AuthenticatorValidateStageDuo";
import "@goauthentik/flow/stages/authenticator_validate/AuthenticatorValidateStageWebAuthn";
import { BaseStage, StageHost, SubmitOptions } from "@goauthentik/flow/stages/base";
import { PasswordManagerPrefill } from "@goauthentik/flow/stages/identification/IdentificationStage";

import { msg } from "@lit/localize";
import { CSSResult, PropertyValues, TemplateResult, css, html, nothing } from "lit";
import { customElement, state } from "lit/decorators.js";

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
    DeviceChallenge,
    DeviceClassesEnum,
    FlowsApi,
} from "@goauthentik/api";

const customCSS = css`
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
`;

@customElement("ak-stage-authenticator-validate")
export class AuthenticatorValidateStage
    extends BaseStage<
        AuthenticatorValidationChallenge,
        AuthenticatorValidationChallengeResponseRequest
    >
    implements StageHost
{
    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFForm, PFFormControl, PFTitle, PFButton, customCSS];
    }

    flowSlug = "";

    set loading(value: boolean) {
        this.host.loading = value;
    }

    get loading(): boolean {
        return this.host.loading;
    }

    get brand(): CurrentBrand | undefined {
        return this.host.brand;
    }

    @state()
    _firstInitialized: boolean = false;

    @state()
    _selectedDeviceChallenge?: DeviceChallenge;

    set selectedDeviceChallenge(value: DeviceChallenge | undefined) {
        const previousChallenge = this._selectedDeviceChallenge;
        this._selectedDeviceChallenge = value;
        if (value === undefined || value === previousChallenge) {
            return;
        }
        // We don't use this.submit here, as we don't want to advance the flow.
        // We just want to notify the backend which challenge has been selected.
        new FlowsApi(DEFAULT_CONFIG).flowsExecutorSolve({
            flowSlug: this.host?.flowSlug || "",
            query: window.location.search.substring(1),
            flowChallengeResponseRequest: {
                // @ts-ignore
                component: this.challenge.component || "",
                selectedChallenge: value,
            },
        });
    }

    get selectedDeviceChallenge(): DeviceChallenge | undefined {
        return this._selectedDeviceChallenge;
    }

    submit(
        payload: AuthenticatorValidationChallengeResponseRequest,
        options?: SubmitOptions,
    ): Promise<boolean> {
        return this.host?.submit(payload, options) || Promise.resolve();
    }

    willUpdate(_changed: PropertyValues<this>) {
        if (this._firstInitialized || !this.challenge) {
            return;
        }

        this._firstInitialized = true;

        // If user only has a single device, autoselect that device.
        if (this.challenge.deviceChallenges.length === 1) {
            this.selectedDeviceChallenge = this.challenge.deviceChallenges[0];
            return;
        }

        // If TOTP is allowed from the backend and we have a pre-filled value
        // from the password manager, autoselect TOTP.
        const totpChallenge = this.challenge.deviceChallenges.find(
            (challenge) => challenge.deviceClass === DeviceClassesEnum.Totp,
        );
        if (PasswordManagerPrefill.totp && totpChallenge) {
            console.debug(
                "authentik/stages/authenticator_validate: found prefill totp code, selecting totp challenge",
            );
            this.selectedDeviceChallenge = totpChallenge;
            return;
        }

        // If the last used device is not Static, autoselect that device.
        const lastUsedChallenge = this.challenge.deviceChallenges
            .filter((deviceChallenge) => deviceChallenge.lastUsed)
            .sort((a, b) => b.lastUsed!.valueOf() - a.lastUsed!.valueOf())[0];
        if (lastUsedChallenge && lastUsedChallenge.deviceClass !== DeviceClassesEnum.Static) {
            this.selectedDeviceChallenge = lastUsedChallenge;
        }
    }

    renderDevicePickerSingle(deviceChallenge: DeviceChallenge) {
        switch (deviceChallenge.deviceClass) {
            case DeviceClassesEnum.Duo:
                return html`<i class="fas fa-mobile-alt"></i>
                    <div class="right">
                        <p>${msg("Duo push-notifications")}</p>
                        <small>${msg("Receive a push notification on your device.")}</small>
                    </div>`;
            case DeviceClassesEnum.Webauthn:
                return html`<i class="fas fa-mobile-alt"></i>
                    <div class="right">
                        <p>${msg("Authenticator")}</p>
                        <small>${msg("Use a security key to prove your identity.")}</small>
                    </div>`;
            case DeviceClassesEnum.Totp:
                return html`<i class="fas fa-clock"></i>
                    <div class="right">
                        <p>${msg("Traditional authenticator")}</p>
                        <small>${msg("Use a code-based authenticator.")}</small>
                    </div>`;
            case DeviceClassesEnum.Static:
                return html`<i class="fas fa-key"></i>
                    <div class="right">
                        <p>${msg("Recovery keys")}</p>
                        <small>${msg("In case you can't access any other method.")}</small>
                    </div>`;
            case DeviceClassesEnum.Sms:
                return html`<i class="fas fa-mobile-alt"></i>
                    <div class="right">
                        <p>${msg("SMS")}</p>
                        <small>${msg("Tokens sent via SMS.")}</small>
                    </div>`;
            case DeviceClassesEnum.Email:
                return html`<i class="fas fa-mobile-alt"></i>
                    <div class="right">
                        <p>${msg("Email")}</p>
                        <small>${msg("Tokens sent via email.")}</small>
                    </div>`;
            default:
                break;
        }
        return nothing;
    }

    renderDevicePicker(): TemplateResult {
        return html`<ul>
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
                            });
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

    renderDeviceChallenge() {
        if (!this.selectedDeviceChallenge) {
            return nothing;
        }
        switch (this.selectedDeviceChallenge?.deviceClass) {
            case DeviceClassesEnum.Static:
            case DeviceClassesEnum.Totp:
            case DeviceClassesEnum.Email:
            case DeviceClassesEnum.Sms:
                return html` <ak-stage-authenticator-validate-code
                    .host=${this}
                    .challenge=${this.challenge}
                    .deviceChallenge=${this.selectedDeviceChallenge}
                    .showBackButton=${(this.challenge?.deviceChallenges || []).length > 1}
                >
                </ak-stage-authenticator-validate-code>`;
            case DeviceClassesEnum.Webauthn:
                return html` <ak-stage-authenticator-validate-webauthn
                    .host=${this}
                    .challenge=${this.challenge}
                    .deviceChallenge=${this.selectedDeviceChallenge}
                    .showBackButton=${(this.challenge?.deviceChallenges || []).length > 1}
                >
                </ak-stage-authenticator-validate-webauthn>`;
            case DeviceClassesEnum.Duo:
                return html` <ak-stage-authenticator-validate-duo
                    .host=${this}
                    .challenge=${this.challenge}
                    .deviceChallenge=${this.selectedDeviceChallenge}
                    .showBackButton=${(this.challenge?.deviceChallenges || []).length > 1}
                >
                </ak-stage-authenticator-validate-duo>`;
        }
        return nothing;
    }

    render(): TemplateResult {
        return this.challenge
            ? html`<header class="pf-c-login__main-header">
                      <h1 class="pf-c-title pf-m-3xl">${this.challenge.flowInfo?.title}</h1>
                  </header>
                  ${this.selectedDeviceChallenge
                      ? this.renderDeviceChallenge()
                      : html`<div class="pf-c-login__main-body">
                                <form class="pf-c-form">
                                    ${this.renderUserInfo()}
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
                            </footer>`}`
            : html`<ak-empty-state loading> </ak-empty-state>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-authenticator-validate": AuthenticatorValidateStage;
    }
}

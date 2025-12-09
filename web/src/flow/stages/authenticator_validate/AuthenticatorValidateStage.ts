import "#flow/components/ak-flow-card";
import "#flow/stages/authenticator_validate/AuthenticatorValidateStageCode";
import "#flow/stages/authenticator_validate/AuthenticatorValidateStageDuo";
import "#flow/stages/authenticator_validate/AuthenticatorValidateStageWebAuthn";

import Styles from "./AuthenticatorValidateStage.css";

import { DEFAULT_CONFIG } from "#common/api/config";

import { BaseStage, StageHost, SubmitOptions } from "#flow/stages/base";
import { PasswordManagerPrefill } from "#flow/stages/identification/IdentificationStage";

import {
    AuthenticatorValidationChallenge,
    AuthenticatorValidationChallengeResponseRequest,
    CurrentBrand,
    DeviceChallenge,
    DeviceClassesEnum,
    FlowChallengeResponseRequest,
    FlowsApi,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, PropertyValues, TemplateResult } from "lit";
import { customElement, state } from "lit/decorators.js";
import { repeat } from "lit/directives/repeat.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";

interface DevicePickerProps {
    icon?: string;
    label: string;
    description?: string;
}

const createDevicePickerPropMap = () =>
    ({
        [DeviceClassesEnum.Duo]: {
            icon: "fa-mobile-alt",
            label: msg("Duo push-notifications"),
            description: msg("Receive a push notification on your device."),
        },
        [DeviceClassesEnum.Webauthn]: {
            icon: "fa-mobile-alt",
            label: msg("Authenticator"),
            description: msg("Use a security key to prove your identity."),
        },
        [DeviceClassesEnum.Totp]: {
            icon: "fa-clock",
            label: msg("Traditional authenticator"),
            description: msg("Use a code-based authenticator."),
        },
        [DeviceClassesEnum.Static]: {
            icon: "fa-key",
            label: msg("Recovery keys"),
            description: msg("In case you lose access to your primary authenticators."),
        },
        [DeviceClassesEnum.Sms]: {
            icon: "fa-mobile-alt",
            label: msg("SMS"),
            description: msg("Tokens sent via SMS."),
        },
        [DeviceClassesEnum.Email]: {
            icon: "fa-envelope",
            label: msg("Email"),
            description: msg("Tokens sent via email."),
        },
        [DeviceClassesEnum.UnknownDefaultOpenApi]: {
            icon: "fa-question",
            label: msg("Unknown device"),
            description: msg("An unknown device class was provided."),
        },
    }) as const satisfies Record<DeviceClassesEnum, DevicePickerProps>;

@customElement("ak-stage-authenticator-validate")
export class AuthenticatorValidateStage
    extends BaseStage<
        AuthenticatorValidationChallenge,
        AuthenticatorValidationChallengeResponseRequest
    >
    implements StageHost
{
    static styles: CSSResult[] = [PFLogin, PFForm, PFFormControl, PFTitle, PFButton, Styles];

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

    #selectedDeviceChallenge?: DeviceChallenge;

    @state()
    protected set selectedDeviceChallenge(value: DeviceChallenge | undefined) {
        const previousChallenge = this.#selectedDeviceChallenge;
        this.#selectedDeviceChallenge = value;

        if (!value || value === previousChallenge) {
            return;
        }

        const component = (this.challenge.component ||
            "") as unknown as "ak-stage-authenticator-validate";

        value.lastUsed ??= new Date();

        const flowChallengeResponseRequest = {
            component,
            selectedChallenge: value,
        } satisfies FlowChallengeResponseRequest;

        // We don't use this.submit here, as we don't want to advance the flow.
        // We just want to notify the backend which challenge has been selected.
        new FlowsApi(DEFAULT_CONFIG).flowsExecutorSolve({
            flowSlug: this.host?.flowSlug || "",
            query: window.location.search.substring(1),
            flowChallengeResponseRequest,
        });
    }

    protected get selectedDeviceChallenge(): DeviceChallenge | undefined {
        return this.#selectedDeviceChallenge;
    }

    public submit(
        payload: AuthenticatorValidationChallengeResponseRequest,
        options?: SubmitOptions,
    ): Promise<boolean> {
        return this.host?.submit(payload, options) || Promise.resolve();
    }

    public reset(): void {
        this.selectedDeviceChallenge = undefined;
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
        const [lastUsedChallenge = null] = this.challenge.deviceChallenges
            .filter((deviceChallenge) => deviceChallenge.lastUsed)
            .sort((a, b) => b.lastUsed!.valueOf() - a.lastUsed!.valueOf());

        if (lastUsedChallenge && lastUsedChallenge.deviceClass !== DeviceClassesEnum.Static) {
            this.selectedDeviceChallenge = lastUsedChallenge;
        }
    }

    renderDevicePicker() {
        const { deviceChallenges } = this.challenge || {};

        if (this.selectedDeviceChallenge || !deviceChallenges?.length) {
            return nothing;
        }

        const devicePickerPropMap = createDevicePickerPropMap();

        const deviceChallengeButtons = repeat(
            deviceChallenges,
            (challenges) => challenges.deviceUid,
            (challenges, idx) => {
                const buttonID = `device-challenge-${idx}`;
                const labelID = `${buttonID}-label`;
                const descriptionID = `${buttonID}-description`;

                const { icon, label, description } = devicePickerPropMap[challenges.deviceClass];

                return html`
                    <button
                        id=${buttonID}
                        aria-labelledby=${labelID}
                        aria-describedby=${descriptionID}
                        class="pf-c-button authenticator-button"
                        type="button"
                        @click=${() => {
                            this.selectedDeviceChallenge = challenges;
                        }}
                    >
                        <i class="fas ${icon}" aria-hidden="true"></i>
                        <div class="content">
                            <h1 class="pf-c-title pf-m-sm" id=${labelID}>${label}</h1>
                            <p class="pf-c-form__helper-text" id=${descriptionID}>${description}</p>
                        </div>
                    </button>
                `;
            },
        );

        return html`<fieldset class="pf-c-form__group pf-m-action" name="device-challenges">
            <legend class="pf-c-title">${msg("Select an authentication method")}</legend>
            ${deviceChallengeButtons}
        </fieldset>`;
    }

    renderStagePicker() {
        if (!this.challenge?.configurationStages.length) {
            return nothing;
        }

        const stageButtons = repeat(
            this.challenge.configurationStages,
            (stage) => stage.pk,
            (stage) => {
                return html`<button
                    class="pf-c-button authenticator-button"
                    type="button"
                    @click=${() => {
                        this.submit({
                            component: this.challenge.component || "",
                            selectedStage: stage.pk,
                        });
                    }}
                >
                    <div class="content">
                        <h1 class="pf-c-title pf-m-sm">${stage.name}</h1>
                        <p class="pf-c-form__helper-text">${stage.verboseName}</p>
                    </div>
                </button>`;
            },
        );

        return html`<fieldset class="pf-c-form__group pf-m-action" name="stages">
            <legend class="sr-only">${msg("Select a configuration stage")}</legend>
            ${stageButtons}
        </fieldset>`;
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

    protected renderAuthenticatorSelection(): TemplateResult {
        return html`<form class="pf-c-form">
            ${this.renderUserInfo()}${this.renderStagePicker()}${this.renderDevicePicker()}
        </form>`;
    }
    render(): TemplateResult {
        return html`<ak-flow-card .challenge=${this.challenge}>
            ${this.selectedDeviceChallenge
                ? this.renderDeviceChallenge()
                : this.renderAuthenticatorSelection()}
        </ak-flow-card>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-authenticator-validate": AuthenticatorValidateStage;
    }
}

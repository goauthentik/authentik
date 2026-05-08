import "#flow/components/ak-flow-card";
import "#flow/stages/authenticator_validate/AuthenticatorValidateStageCode";
import "#flow/stages/authenticator_validate/AuthenticatorValidateStageDuo";
import "#flow/stages/authenticator_validate/AuthenticatorValidateStageWebAuthn";

import Styles from "./AuthenticatorValidateStage.css";

import { DEFAULT_CONFIG } from "#common/api/config";

import { SlottedTemplateResult } from "#elements/types";
import { StrictUnsafe } from "#elements/utils/unsafe";

import { shouldResetSelectedChallenge } from "#flow/stages/authenticator_validate/challenge-selection";
import { BaseStage } from "#flow/stages/base";
import { PasswordManagerPrefill } from "#flow/stages/identification/IdentificationStage";
import type { StageHost, SubmitOptions } from "#flow/types";

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
            label: msg("Security key"),
            description: msg("Use a Passkey or security key to prove your identity."),
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
            icon: "fa-comment",
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

export function resolveAuthenticatorComponentTag(
    deviceClass: DeviceClassesEnum | null | undefined,
) {
    switch (deviceClass) {
        case DeviceClassesEnum.Static:
        case DeviceClassesEnum.Totp:
        case DeviceClassesEnum.Email:
        case DeviceClassesEnum.Sms:
            return "ak-stage-authenticator-validate-code";
        case DeviceClassesEnum.Webauthn:
            return "ak-stage-authenticator-validate-webauthn";
        case DeviceClassesEnum.Duo:
            return "ak-stage-authenticator-validate-duo";
        default:
            return null;
    }
}

@customElement("ak-stage-authenticator-validate")
export class AuthenticatorValidateStage
    extends BaseStage<
        AuthenticatorValidationChallenge,
        AuthenticatorValidationChallengeResponseRequest
    >
    implements StageHost
{
    static styles: CSSResult[] = [
        // ---
        PFLogin,
        PFForm,
        PFFormControl,
        PFTitle,
        PFButton,
        Styles,
    ];

    #api = new FlowsApi(DEFAULT_CONFIG);

    public flowSlug = "";

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
    protected initialized = false;

    #selectedDeviceChallenge: DeviceChallenge | null = null;

    @state()
    protected set selectedDeviceChallenge(value: DeviceChallenge | null) {
        const previousChallenge = this.#selectedDeviceChallenge;
        this.#selectedDeviceChallenge = value;

        if (!value || value === previousChallenge) {
            return;
        }

        const component = (this.challenge?.component ||
            "") as unknown as "ak-stage-authenticator-validate";

        value.lastUsed ??= new Date();

        const flowChallengeResponseRequest = {
            component,
            selectedChallenge: value,
        } satisfies FlowChallengeResponseRequest;

        // We don't use this.submit here, as we don't want to advance the flow.
        // We just want to notify the backend which challenge has been selected.
        this.#api.flowsExecutorSolve({
            flowSlug: this.host?.flowSlug || "",
            query: window.location.search.substring(1),
            flowChallengeResponseRequest,
        });
    }

    protected get selectedDeviceChallenge(): DeviceChallenge | null {
        return this.#selectedDeviceChallenge;
    }

    public submit(
        payload: AuthenticatorValidationChallengeResponseRequest,
        options?: SubmitOptions,
    ): Promise<boolean> {
        return this.host?.submit(payload, options) || Promise.resolve();
    }

    public reset(): void {
        this.selectedDeviceChallenge = null;
    }

    protected override willUpdate(changed: PropertyValues<this>) {
        // When moving between multiple authenticator-validate stages in one flow, the element
        // instance is reused. Reset selection if it is no longer valid in the new challenge.
        if (changed.has("challenge")) {
            const allowedChallenges = this.challenge?.deviceChallenges ?? [];

            if (shouldResetSelectedChallenge(this.selectedDeviceChallenge, allowedChallenges)) {
                this.selectedDeviceChallenge = null;
                this.initialized = false;
            }
        }

        if (this.initialized || !this.challenge) {
            return;
        }

        this.initialized = true;

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
            this.logger.debug("Found prefill TOTP code to select");
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

    protected renderDevicePicker(): SlottedTemplateResult {
        const { deviceChallenges } = this.challenge || {};

        if (!deviceChallenges?.length) {
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

        return html`<fieldset
            class="ak-c-fieldset pf-c-form__group pf-m-action"
            name="device-challenges"
        >
            <legend class="pf-c-title">${msg("Select an authentication method")}</legend>
            ${deviceChallengeButtons}
        </fieldset>`;
    }

    protected renderStagePicker(): SlottedTemplateResult {
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
                            component: this.challenge?.component || "",
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

        return html`<fieldset class="ak-c-fieldset pf-c-form__group pf-m-action" name="stages">
            <legend class="sr-only">${msg("Select a configuration stage")}</legend>
            ${stageButtons}
        </fieldset>`;
    }

    protected renderDeviceChallenge() {
        if (!this.selectedDeviceChallenge) {
            return nothing;
        }

        const tag = resolveAuthenticatorComponentTag(this.selectedDeviceChallenge.deviceClass);
        if (!tag) return null;

        const showBackButton = (this.challenge?.deviceChallenges || []).length > 1;

        return StrictUnsafe(tag, {
            host: this,
            challenge: this.challenge,
            deviceChallenge: this.selectedDeviceChallenge,
            showBackButton,
        });
    }

    protected renderAuthenticatorSelection(): TemplateResult {
        return html`<form class="pf-c-form">
            ${this.renderUserInfo()}${this.renderStagePicker()}${this.renderDevicePicker()}
        </form>`;
    }

    protected override render(): TemplateResult {
        return html`<ak-flow-card .challenge=${this.challenge}>
            ${this.selectedDeviceChallenge
                ? this.renderDeviceChallenge()
                : this.renderAuthenticatorSelection()}
        </ak-flow-card>`;
    }
}

export default AuthenticatorValidateStage;

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-authenticator-validate": AuthenticatorValidateStage;
    }
}

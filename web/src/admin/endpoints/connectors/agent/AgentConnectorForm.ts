import "#components/ak-secret-text-input";
import "#components/ak-text-input";
import "#components/ak-number-input";
import "#components/ak-switch-input";
import "#components/ak-radio-input";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/FormGroup";
import "#admin/common/ak-flow-search/ak-flow-search";
import "#admin/common/ak-crypto-certificate-search";
import "#elements/utils/TimeDeltaHelp";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#elements/ak-array-input";

import { aki } from "#common/api/client";

import { ModelForm } from "#elements/forms/ModelForm";
import { RadioChangeEventDetail, RadioOption } from "#elements/forms/Radio";
import { WithBrandConfig } from "#elements/mixins/branding";
import { ifPresent } from "#elements/utils/attributes";

import {
    oauth2ProvidersProvider,
    oauth2ProvidersSelector,
} from "#admin/providers/oauth2/OAuth2ProvidersProvider";

import {
    AgentConnector,
    AgentConnectorRequest,
    ApplePssoAuthenticationMethodEnum,
    ApplePssoBiometricRequirementEnum,
    ApplePssoFilevaultPolicyEnum,
    EndpointsApi,
    FlowDesignationEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-endpoints-connector-agent-form")
export class AgentConnectorForm extends WithBrandConfig(ModelForm<AgentConnector, string>) {
    // Apple treats the Platform SSO authentication method as a single mode, and each mode
    // ignores the other's settings, so the form only offers the group that applies.
    @state()
    protected selectedAuthenticationMethod: ApplePssoAuthenticationMethodEnum =
        ApplePssoAuthenticationMethodEnum.UserSecureEnclaveKey;

    #authenticationMethodChangeListener = (
        event: CustomEvent<RadioChangeEventDetail<ApplePssoAuthenticationMethodEnum>>,
    ): void => {
        this.selectedAuthenticationMethod = event.detail.value;
    };

    protected endpoints = {
        load: async (connectorUuid: string) => {
            const connector = await aki(EndpointsApi).endpointsAgentsConnectorsRetrieve({
                connectorUuid,
            });
            this.selectedAuthenticationMethod =
                connector.applePssoAuthenticationMethod ??
                ApplePssoAuthenticationMethodEnum.UserSecureEnclaveKey;
            return connector;
        },
        create: (data: AgentConnector) =>
            aki(EndpointsApi).endpointsAgentsConnectorsCreate({
                agentConnectorRequest: data as unknown as AgentConnectorRequest,
            }),
        update: (connectorUuid: string, patchedAgentConnectorRequest: AgentConnector) =>
            aki(EndpointsApi).endpointsAgentsConnectorsPartialUpdate({
                connectorUuid,
                patchedAgentConnectorRequest,
            }),
    };

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated agent connector.")
            : msg("Successfully created agent connector.");
    }

    renderForm() {
        const pssoBiometricOptions = [
            {
                label: msg("None (no biometric required)"),
                value: ApplePssoBiometricRequirementEnum.None,
            },
            {
                label: msg("Touch ID or Apple Watch, invalidated if enrolment changes"),
                value: ApplePssoBiometricRequirementEnum.CurrentSet,
            },
            {
                label: msg("Touch ID or Apple Watch, any enrolment"),
                value: ApplePssoBiometricRequirementEnum.Any,
            },
        ];
        const pssoAuthenticationMethodOptions = [
            {
                label: msg("User Secure Enclave key"),
                value: ApplePssoAuthenticationMethodEnum.UserSecureEnclaveKey,
                description: html`${msg(
                    "The Mac authenticates with a hardware-backed key and the local account password is left alone. Users may fall back to their authentik password when a required biometric is unavailable.",
                )}`,
            },
            {
                label: msg("Password"),
                value: ApplePssoAuthenticationMethodEnum.Password,
                description: html`${msg(
                    "Users sign in to the Mac with their authentik password, and the local account password is kept in sync with it.",
                )}`,
            },
        ];
        const pssoPolicyOptions = [
            {
                label: msg("None (silent background token only)"),
                value: ApplePssoFilevaultPolicyEnum.None,
            },
            {
                label: msg("Attempt authentication (enforced only when online)"),
                value: ApplePssoFilevaultPolicyEnum.Attempt,
            },
            {
                label: msg("Require authentication"),
                value: ApplePssoFilevaultPolicyEnum.Require,
            },
        ];
        return html`<ak-text-input
                name="name"
                placeholder=${msg("Type a connector name...")}
                label=${msg("Connector name")}
                value=${ifDefined(this.instance?.name)}
                input-hint="code"
                autofocus
                required
            ></ak-text-input>
            <ak-text-input
                name="refreshInterval"
                label=${msg("Refresh interval")}
                input-hint="code"
                required
                value="${ifDefined(this.instance?.refreshInterval ?? "minutes=30")}"
                .bighelp=${html`<p class="pf-c-form__helper-text">
                        ${msg("Interval how frequently the agent tries to update its config.")}
                    </p>
                    <ak-utils-time-delta-help></ak-utils-time-delta-help>`}
            >
            </ak-text-input>
            <ak-switch-input
                name="enabled"
                label=${msg("Enabled")}
                ?checked=${this.instance?.enabled ?? true}
            >
            </ak-switch-input>
            <ak-form-group label="${msg("Authentication settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Authorization Flow")}
                        name="authorizationFlow"
                    >
                        <ak-flow-search
                            label=${msg("Authorization Flow")}
                            flowType=${FlowDesignationEnum.Authorization}
                            .currentFlow=${this.instance?.authorizationFlow}
                        ></ak-flow-search>
                        <p class="pf-c-form__helper-text">
                            ${msg("Flow used for users to authorize.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-text-input
                        name="authSessionDuration"
                        label=${msg("Session duration")}
                        input-hint="code"
                        required
                        value="${ifDefined(this.instance?.authSessionDuration ?? "hours=8")}"
                        .bighelp=${html`<p class="pf-c-form__helper-text">
                                ${msg("Configure how long an authenticated session is valid for.")}
                            </p>
                            <ak-utils-time-delta-help></ak-utils-time-delta-help>`}
                    >
                    </ak-text-input>
                    <ak-switch-input
                        name="authTerminateSessionOnExpiry"
                        label=${msg("Terminate authenticated sessions on token expiry")}
                        ?checked=${this.instance?.authTerminateSessionOnExpiry ?? true}
                    >
                    </ak-switch-input>
                    <ak-form-element-horizontal
                        label=${msg("Federated OAuth2/OpenID Providers")}
                        name="jwtFederationProviders"
                    >
                        <ak-dual-select-dynamic-selected
                            .provider=${oauth2ProvidersProvider}
                            .selector=${oauth2ProvidersSelector(
                                this.instance?.jwtFederationProviders,
                            )}
                            available-label=${msg("Available Providers")}
                            selected-label=${msg("Selected Providers")}
                        ></ak-dual-select-dynamic-selected>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "JWTs signed by the selected providers can be used to authenticate to devices.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group label="${msg("Device compliance settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Challenge certificate")}
                        name="challengeKey"
                    >
                        <ak-crypto-certificate-search
                            label=${msg("Certificate")}
                            placeholder=${msg("Select a certificate...")}
                            certificate=${ifPresent(this.instance?.challengeKey)}
                            name="certificate"
                        >
                        </ak-crypto-certificate-search>
                        <p class="pf-c-form__helper-text">
                            ${msg("Certificate used for signing device compliance challenges.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-text-input
                        name="challengeIdleTimeout"
                        label=${msg("Challenge idle timeout")}
                        input-hint="code"
                        required
                        value="${ifDefined(this.instance?.challengeIdleTimeout ?? "seconds=3")}"
                        .bighelp=${html`<p class="pf-c-form__helper-text">
                                ${msg(
                                    "Duration the flow executor will wait before continuing without a response.",
                                )}
                            </p>
                            <ak-utils-time-delta-help></ak-utils-time-delta-help>`}
                    >
                    </ak-text-input>
                    <ak-switch-input
                        name="challengeTriggerCheckIn"
                        label=${msg("Trigger check-in on device")}
                        ?checked=${this.instance?.challengeTriggerCheckIn ?? true}
                    >
                    </ak-switch-input>
                </div>
            </ak-form-group>
            <ak-form-group label="${msg("Unix settings")}">
                <div class="pf-c-form">
                    <ak-number-input
                        label=${msg("NSS User ID offset")}
                        required
                        name="nssUidOffset"
                        value="${this.instance?.nssUidOffset ?? 2000}"
                        help=${msg(
                            "The start for user ID numbers, this number is added to the user ID to make sure that the numbers aren't too low for POSIX users. Default is 2000 to prevent collisions with local users.",
                        )}
                    ></ak-number-input>
                    <ak-number-input
                        label=${msg("NSS Group ID offset")}
                        required
                        name="nssGidOffset"
                        value="${this.instance?.nssGidOffset ?? 4000}"
                        help=${msg(
                            "The start for group ID numbers, this number is added to a number generated from the groups' ID to make sure that the numbers aren't too low for POSIX groups. Default is 4000 to prevent collisions with local groups.",
                        )}
                    ></ak-number-input>
                </div>
            </ak-form-group>
            <ak-form-group label="${msg("Apple Platform SSO (macOS)")}">
                <div class="pf-c-form">
                    <p class="pf-c-form__helper-text">
                        ${msg(
                            "These settings only affect macOS devices enrolled via this connector. When every policy is left at its default, Platform SSO runs silently and acquires SSO tokens in the background without prompting at the login window.",
                        )}
                    </p>
                    <ak-radio-input
                        @change=${this.#authenticationMethodChangeListener}
                        name="applePssoAuthenticationMethod"
                        label=${msg("Authentication method")}
                        required
                        .options=${pssoAuthenticationMethodOptions}
                        .value=${this.selectedAuthenticationMethod}
                        help=${msg(
                            "How users prove who they are at the macOS login window. Changing this only affects devices enrolled after the change.",
                        )}
                    ></ak-radio-input>
                    <ak-number-input
                        name="applePssoLoginFrequency"
                        label=${msg("Login frequency")}
                        required
                        value="${this.instance?.applePssoLoginFrequency ?? 64800}"
                        help=${msg(
                            "Maximum interval, in seconds, before a full re-authentication is required. Apple default is 64800 (18 hours); minimum is 3600 (1 hour).",
                        )}
                    ></ak-number-input>
                    ${this.selectedAuthenticationMethod ===
                    ApplePssoAuthenticationMethodEnum.Password
                        ? this.renderPasswordModeOptions(pssoPolicyOptions)
                        : this.renderSecureEnclaveModeOptions(pssoBiometricOptions)}
                </div>
            </ak-form-group>`;
    }

    protected renderPasswordModeOptions(pssoPolicyOptions: RadioOption<string>[]) {
        return html`<ak-radio-input
                name="applePssoLoginPolicy"
                label=${msg("Login window policy")}
                .options=${pssoPolicyOptions}
                .value=${this.instance?.applePssoLoginPolicy ?? ApplePssoFilevaultPolicyEnum.None}
                help=${msg(
                    "Whether Platform SSO authenticates the user against authentik at the macOS login window.",
                )}
            ></ak-radio-input>
            <ak-radio-input
                name="applePssoUnlockPolicy"
                label=${msg("Screen unlock policy")}
                .options=${pssoPolicyOptions}
                .value=${this.instance?.applePssoUnlockPolicy ?? ApplePssoFilevaultPolicyEnum.None}
                help=${msg(
                    "Whether Platform SSO authenticates the user against authentik when unlocking the screen.",
                )}
            ></ak-radio-input>
            <ak-radio-input
                name="applePssoFilevaultPolicy"
                label=${msg("FileVault policy")}
                .options=${pssoPolicyOptions}
                .value=${this.instance?.applePssoFilevaultPolicy ??
                ApplePssoFilevaultPolicyEnum.None}
                help=${msg(
                    "Whether Platform SSO authenticates the user against authentik at FileVault unlock after a restart.",
                )}
            ></ak-radio-input>
            <ak-number-input
                name="applePssoAuthenticationGracePeriod"
                label=${msg("Authentication grace period")}
                value="${this.instance?.applePssoAuthenticationGracePeriod ?? 0}"
                help=${msg(
                    "Seconds after a policy is applied during which accounts that have not yet registered with Platform SSO can still sign in. 0 disables the grace period.",
                )}
            ></ak-number-input>
            <ak-number-input
                name="applePssoOfflineGracePeriod"
                label=${msg("Offline grace period")}
                value="${this.instance?.applePssoOfflineGracePeriod ?? 0}"
                help=${msg(
                    "Seconds after the last successful Platform SSO login that the local account password keeps working while the Mac is offline. 0 disables the grace period.",
                )}
            ></ak-number-input>
            <ak-form-element-horizontal
                label=${msg("Exempt local accounts")}
                name="applePssoNonPlatformSsoAccounts"
            >
                <ak-array-input
                    .items=${this.instance?.applePssoNonPlatformSsoAccounts ?? []}
                    .newItem=${() => ""}
                    .row=${(item?: string) =>
                        html`<ak-text-input
                            name="non-platform-sso-account"
                            style="width: 100%"
                            value=${ifDefined(item)}
                            required
                        ></ak-text-input>`}
                >
                </ak-array-input>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Local accounts that the policies above do not apply to, and that are never prompted to register. Add a break-glass administrator here before requiring authentication, otherwise an unreachable authentik locks every account out of the Mac.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-switch-input
                name="applePssoEnableCreateUserAtLogin"
                label=${msg("Create users at the login window")}
                ?checked=${this.instance?.applePssoEnableCreateUserAtLogin ?? false}
                help=${msg(
                    "Let a user with no local account sign in at the login window and have an account created for them.",
                )}
            >
            </ak-switch-input>`;
    }

    protected renderSecureEnclaveModeOptions(pssoBiometricOptions: RadioOption<string>[]) {
        return html`<ak-radio-input
                name="applePssoBiometricRequirement"
                label=${msg("Biometric requirement")}
                .options=${pssoBiometricOptions}
                .value=${this.instance?.applePssoBiometricRequirement ??
                ApplePssoBiometricRequirementEnum.None}
                help=${msg(
                    "Which biometric, if any, is required to use the Secure Enclave key. Requires native agent support.",
                )}
            ></ak-radio-input>
            <ak-switch-input
                name="applePssoBiometricPasswordFallback"
                label=${msg("Allow password fallback")}
                ?checked=${this.instance?.applePssoBiometricPasswordFallback ?? true}
                help=${msg(
                    "Offer 'log in with authentik password instead' when Touch ID is cancelled, fails, or was never enrolled. Turning this off will lock out users on Macs with no Touch ID hardware.",
                )}
            >
            </ak-switch-input>
            <ak-switch-input
                name="applePssoBiometricReuseDuringUnlock"
                label=${msg("Reuse Touch ID from unlock")}
                ?checked=${this.instance?.applePssoBiometricReuseDuringUnlock ?? false}
                help=${msg(
                    "Reuse the Touch ID presented when unlocking the Mac instead of prompting again.",
                )}
            >
            </ak-switch-input>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-connector-agent-form": AgentConnectorForm;
    }
}

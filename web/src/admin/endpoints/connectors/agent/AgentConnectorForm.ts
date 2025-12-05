import "#components/ak-secret-text-input";
import "#components/ak-text-input";
import "#components/ak-number-input";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/FormGroup";
import "#admin/common/ak-flow-search/ak-flow-search";
import "#admin/common/ak-crypto-certificate-search";
import "#elements/utils/TimeDeltaHelp";

import { DEFAULT_CONFIG } from "#common/api/config";

import { ModelForm } from "#elements/forms/ModelForm";
import { WithBrandConfig } from "#elements/mixins/branding";
import { ifPresent } from "#elements/utils/attributes";

import { gidStartNumberHelp, uidStartNumberHelp } from "#admin/providers/ldap/LDAPOptionsAndHelp";
import {
    oauth2ProvidersProvider,
    oauth2ProvidersSelector,
} from "#admin/providers/oauth2/OAuth2ProvidersProvider";

import {
    AgentConnector,
    AgentConnectorRequest,
    EndpointsApi,
    FlowsInstancesListDesignationEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-endpoints-connector-agent-form")
export class AgentConnectorForm extends WithBrandConfig(ModelForm<AgentConnector, string>) {
    loadInstance(pk: string): Promise<AgentConnector> {
        return new EndpointsApi(DEFAULT_CONFIG).endpointsAgentsConnectorsRetrieve({
            connectorUuid: pk,
        });
    }

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated agent connector.")
            : msg("Successfully created agent connector.");
    }

    async send(data: AgentConnector): Promise<AgentConnector> {
        if (this.instance) {
            return new EndpointsApi(DEFAULT_CONFIG).endpointsAgentsConnectorsPartialUpdate({
                connectorUuid: this.instance.connectorUuid!,
                patchedAgentConnectorRequest: data,
            });
        }
        return new EndpointsApi(DEFAULT_CONFIG).endpointsAgentsConnectorsCreate({
            agentConnectorRequest: data as unknown as AgentConnectorRequest,
        });
    }

    renderForm() {
        return html`<ak-text-input
                name="name"
                placeholder=${msg("Connector name...")}
                label=${msg("Connector name")}
                value=${ifDefined(this.instance?.name)}
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
            <ak-form-element-horizontal name="enabled">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${this.instance?.enabled ?? true}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${msg("Enabled")}</span>
                </label>
            </ak-form-element-horizontal>
            <ak-form-group label="${msg("Authentication settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Authorization flow")}
                        name="authorizationFlow"
                    >
                        <ak-flow-search
                            label=${msg("Authorization flow")}
                            flowType=${FlowsInstancesListDesignationEnum.Authorization}
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
                    <ak-form-element-horizontal name="authTerminateSessionOnExpiry">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${this.instance?.authTerminateSessionOnExpiry ?? true}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label"
                                >${msg("Terminate authenticated sessions on token expiry")}</span
                            >
                        </label>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Federated OIDC Providers")}
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
                    <ak-form-element-horizontal name="challengeTriggerCheckIn">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${this.instance?.challengeTriggerCheckIn ?? true}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label"
                                >${msg("Trigger check-in on device")}</span
                            >
                        </label>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group label="${msg("Unix settings")}">
                <div class="pf-c-form">
                    <ak-number-input
                        label=${msg("NSS User ID offset")}
                        required
                        name="nssUidOffset"
                        value="${this.instance?.nssUidOffset ?? 1000}"
                        help=${uidStartNumberHelp}
                    ></ak-number-input>
                    <ak-number-input
                        label=${msg("NSS Group ID offset")}
                        required
                        name="nssGidOffset"
                        value="${this.instance?.nssGidOffset ?? 1000}"
                        help=${gidStartNumberHelp}
                    ></ak-number-input>
                </div>
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-connector-agent-form": AgentConnectorForm;
    }
}

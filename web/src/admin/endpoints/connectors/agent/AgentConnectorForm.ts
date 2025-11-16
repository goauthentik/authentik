import "#components/ak-secret-text-input";
import "#components/ak-text-input";
import "#components/ak-number-input";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/FormGroup";
import "#admin/common/ak-flow-search/ak-branded-flow-search";
import "#admin/common/ak-crypto-certificate-search";

import { DEFAULT_CONFIG } from "#common/api/config";

import { ModelForm } from "#elements/forms/ModelForm";

import { AgentConnector, EndpointsApi, AgentConnectorRequest, FlowsInstancesListDesignationEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { WithBrandConfig } from "#elements/mixins/branding";
import { ifPresent } from "#elements/utils/attributes";

@customElement("ak-endpoints-connector-agent")
export class AgentConnectorForm extends WithBrandConfig(ModelForm<AgentConnector, string>) {
    loadInstance(pk: string): Promise<AgentConnector> {
        return new EndpointsApi(DEFAULT_CONFIG).endpointsAgentsConnectorsRetrieve({
            connectorUuid: pk,
        });
    }

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated connector.")
            : msg("Successfully created connector.");
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
            <ak-form-element-horizontal
                label=${msg("Authentication flow")}
                required
                name="authenticationFlow"
            >
                <ak-branded-flow-search
                    label=${msg("Bind flow")}
                    flowType=${FlowsInstancesListDesignationEnum.Authentication}
                    .currentFlow=${this.instance?.authenticationFlow}
                    .brandFlow=${this.brand?.flowAuthentication}
                    required
                ></ak-branded-flow-search>
                <p class="pf-c-form__helper-text">
                    ${msg("Flow used for users to authenticate.")}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Certificate")}
                name="challengeKey"
            >
                <ak-crypto-certificate-search
                    label=${msg("Certificate")}
                    placeholder=${msg("Select a certificate...")}
                    certificate=${ifPresent(this.instance?.challengeKey)}
                    name="certificate"
                >
                </ak-crypto-certificate-search>
                <p class="pf-c-form__helper-text">${msg("Certificate used for signing device compliance challenges.")}</p>
            </ak-form-element-horizontal>
            <ak-form-group open label="${msg("Unix settings")}">
                <div class="pf-c-form">
                    <ak-number-input
                        label=${msg("NSS User ID offset")}
                        required
                        name="nssUidOffset"
                        value="${this.instance?.nssUidOffset ?? 1000}"
                        help=${msg("Reputation cannot decrease lower than this value. Zero or negative.")}
                    ></ak-number-input>
                    <ak-number-input
                        label=${msg("NSS Group ID offset")}
                        required
                        name="nssGidOffset"
                        value="${this.instance?.nssGidOffset ?? 1000}"
                        help=${msg("Reputation cannot decrease lower than this value. Zero or negative.")}
                    ></ak-number-input>
                </div>
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-connector-agent": AgentConnectorForm;
    }
}

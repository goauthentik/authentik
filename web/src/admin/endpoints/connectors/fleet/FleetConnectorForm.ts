import "#components/ak-secret-text-input";
import "#components/ak-text-input";
import "#elements/forms/HorizontalFormElement";

import { DEFAULT_CONFIG } from "#common/api/config";

import { ModelForm } from "#elements/forms/ModelForm";

import { EndpointsApi, FleetConnector, FleetConnectorRequest } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-endpoints-connector-fleet-form")
export class FleetConnectorForm extends ModelForm<FleetConnector, string> {
    loadInstance(pk: string): Promise<FleetConnector> {
        return new EndpointsApi(DEFAULT_CONFIG).endpointsFleetConnectorsRetrieve({
            connectorUuid: pk,
        });
    }

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated fleet connector.")
            : msg("Successfully created fleet connector.");
    }

    async send(data: FleetConnector): Promise<FleetConnector> {
        if (this.instance) {
            return new EndpointsApi(DEFAULT_CONFIG).endpointsFleetConnectorsPartialUpdate({
                connectorUuid: this.instance.connectorUuid!,
                patchedFleetConnectorRequest: data,
            });
        }
        return new EndpointsApi(DEFAULT_CONFIG).endpointsFleetConnectorsCreate({
            fleetConnectorRequest: data as unknown as FleetConnectorRequest,
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
            <ak-text-input
                name="url"
                label=${msg("Fleet Server URL")}
                value="${ifDefined(this.instance?.url)}"
                required
                input-hint="code"
            >
            </ak-text-input>
            <ak-secret-text-input
                label=${msg("Fleet API Token")}
                name="token"
                ?revealed=${!this.instance}
            ></ak-secret-text-input> `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-connector-fleet-form": FleetConnectorForm;
    }
}

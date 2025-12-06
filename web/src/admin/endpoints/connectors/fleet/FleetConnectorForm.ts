import "#components/ak-secret-text-input";
import "#components/ak-switch-input";
import "#components/ak-text-input";
import "#elements/forms/HorizontalFormElement";

import { DEFAULT_CONFIG } from "#common/api/config";

import { ModelForm } from "#elements/forms/ModelForm";

import { EndpointsApi, FleetConnector, FleetConnectorRequest } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-endpoints-connector-fleet-form")
export class FleetConnectorForm extends ModelForm<FleetConnector, string> {
    loadInstance(pk: string): Promise<FleetConnector> {
        return new EndpointsApi(DEFAULT_CONFIG).endpointsFleetConnectorsRetrieve({
            connectorUuid: pk,
        });
    }

    public override getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated Fleet connector.")
            : msg("Successfully created Fleet connector.");
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
                value=${this.instance?.name ?? ""}
                required
            ></ak-text-input>
            <ak-switch-input
            name="enabled"
            label=${msg("Enabled")}
              ?checked=${this.instance?.enabled ?? true}
            ></ak-switch-input>
            <ak-text-input
                name="url"
                label=${msg("Fleet Server URL")}
                value=${this.instance?.url ?? ""}
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

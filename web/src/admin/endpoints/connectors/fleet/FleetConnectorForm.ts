import "#components/ak-secret-text-input";
import "#components/ak-switch-input";
import "#components/ak-text-input";
import "#elements/forms/FormGroup";

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
            <ak-form-group label=${msg("Fleet settings")} open>
                <div class="pf-c-form">
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
                    ></ak-secret-text-input>
                    <ak-switch-input
                        name="mapUsers"
                        label=${msg("Map users")}
                        ?checked=${this.instance?.mapUsers ?? true}
                        help=${msg(
                            "When enabled, users detected by Fleet will be mapped in authentik, granting them access to the device.",
                        )}
                    ></ak-switch-input>
                    <ak-switch-input
                        name="mapTeamsAccessGroup"
                        label=${msg("Map teams to device access group")}
                        ?checked=${this.instance?.mapTeamsAccessGroup ?? false}
                        help=${msg(
                            "When enabled, Fleet teams will be mapped to Device access groups. Missing device access groups are automatically created. Devices assigned to a different group are not re-assigned",
                        )}
                    ></ak-switch-input>
                </div>
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-connector-fleet-form": FleetConnectorForm;
    }
}

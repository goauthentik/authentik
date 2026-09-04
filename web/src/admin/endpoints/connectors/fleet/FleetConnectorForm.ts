import "#components/ak-secret-search-input";
import "#components/ak-switch-input";
import "#components/ak-text-input";
import "#elements/forms/FormGroup";

import { aki } from "#common/api/client";

import { ModelForm } from "#elements/forms/ModelForm";
import { ifPresent } from "#elements/utils/attributes";

import { EndpointsApi, FleetConnector, FleetConnectorRequest } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-endpoints-connector-fleet-form")
export class FleetConnectorForm extends ModelForm<FleetConnector, string> {
    protected endpoints = {
        load: (connectorUuid: string) =>
            aki(EndpointsApi).endpointsFleetConnectorsRetrieve({
                connectorUuid,
            }),
        create: (data: FleetConnector) =>
            aki(EndpointsApi).endpointsFleetConnectorsCreate({
                fleetConnectorRequest: data as unknown as FleetConnectorRequest,
            }),
        update: (connectorUuid: string, patchedFleetConnectorRequest: FleetConnector) =>
            aki(EndpointsApi).endpointsFleetConnectorsPartialUpdate({
                connectorUuid,
                patchedFleetConnectorRequest,
            }),
    };

    public override getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated Fleet connector.")
            : msg("Successfully created Fleet connector.");
    }

    renderForm() {
        return html`<ak-text-input
                name="name"
                autofocus
                placeholder=${msg("Type a connector name...")}
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
                        inputmode="url"
                        value=${this.instance?.url ?? ""}
                        required
                        input-hint="code"
                    >
                    </ak-text-input>
                    <ak-secret-search-input
                        name="secret"
                        label=${msg("Fleet API Token")}
                        value=${ifPresent(this.instance?.secret ?? undefined)}
                        required
                        help=${msg("Token used to authenticate against the Fleet server.", {
                            id: "connector.fleet.form.secret.description",
                        })}
                    ></ak-secret-search-input>
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

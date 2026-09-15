import "#components/ak-secret-search-input";
import "#components/ak-switch-input";
import "#components/ak-text-input";
import "#elements/forms/FormGroup";

import { aki } from "#common/api/client";

import { ModelForm } from "#elements/forms/ModelForm";
import { ifPresent } from "#elements/utils/attributes";

import { EndpointsApi, GoogleChromeConnector } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-endpoints-connector-gdtc-form")
export class GoogleChromeConnectorForm extends ModelForm<GoogleChromeConnector, string> {
    protected endpoints = {
        load: (connectorUuid: string) =>
            aki(EndpointsApi).endpointsGoogleChromeConnectorsRetrieve({
                connectorUuid,
            }),
        create: (googleChromeConnectorRequest: GoogleChromeConnector) =>
            aki(EndpointsApi).endpointsGoogleChromeConnectorsCreate({
                googleChromeConnectorRequest,
            }),
        update: (
            connectorUuid: string,
            patchedGoogleChromeConnectorRequest: GoogleChromeConnector,
        ) =>
            aki(EndpointsApi).endpointsGoogleChromeConnectorsPartialUpdate({
                connectorUuid,
                patchedGoogleChromeConnectorRequest,
            }),
    };

    public override getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated Google Chrome connector.")
            : msg("Successfully created Google Chrome connector.");
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
            <ak-form-group label=${msg("Google settings")} open>
                <div class="pf-c-form">
                    <ak-secret-search-input
                        name="secret"
                        label=${msg("Credentials", { id: "google.credentials.label" })}
                        value=${ifPresent(this.instance?.secret)}
                        required
                        help=${msg(
                            "Select a secret containing the Google Cloud credentials JSON file.",
                            { id: "google.credentials.description" },
                        )}
                    ></ak-secret-search-input>
                </div>
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-connector-gdtc-form": GoogleChromeConnectorForm;
    }
}

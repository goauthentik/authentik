import "#components/ak-secret-text-input";
import "#components/ak-switch-input";
import "#components/ak-text-input";
import "#elements/forms/FormGroup";
import "#elements/CodeMirror";
import { aki } from "#common/api/client";

import { ModelForm } from "#elements/forms/ModelForm";

import { EndpointsApi, GoogleChromeConnector } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-endpoints-connector-gdtc-form")
export class GoogleChromeConnectorForm extends ModelForm<GoogleChromeConnector, string> {
    loadInstance(pk: string): Promise<GoogleChromeConnector> {
        return aki(EndpointsApi).endpointsGoogleChromeConnectorsRetrieve({
            connectorUuid: pk,
        });
    }

    public override getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated Google Chrome connector.")
            : msg("Successfully created Google Chrome connector.");
    }

    async send(data: GoogleChromeConnector): Promise<GoogleChromeConnector> {
        if (this.instance) {
            return aki(EndpointsApi).endpointsGoogleChromeConnectorsPartialUpdate({
                connectorUuid: this.instance.connectorUuid!,
                patchedGoogleChromeConnectorRequest: data,
            });
        }

        return aki(EndpointsApi).endpointsGoogleChromeConnectorsCreate({
            googleChromeConnectorRequest: data,
        });
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
                    <ak-form-element-horizontal
                        label=${msg("Credentials")}
                        required
                        name="credentials"
                    >
                        <ak-codemirror
                            mode="javascript"
                            .value="${this.instance?.credentials ?? {}}"
                        ></ak-codemirror>
                        <p class="pf-c-form__helper-text">
                            ${msg("Google Cloud credentials file.")}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-connector-gdtc-form": GoogleChromeConnectorForm;
    }
}

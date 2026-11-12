import "#components/ak-secret-text-input";
import "#components/ak-switch-input";
import "#components/ak-text-input";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import { aki } from "#common/api/client";

import { ModelForm } from "#elements/forms/ModelForm";

import { certificateProvider, certificateSelector } from "#admin/brands/Certificates";

import {
    EndpointsApi,
    MicrosoftIntuneConnector,
    MicrosoftIntuneConnectorRequest,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-endpoints-connector-microsoft-intune-form")
export class MicrosoftIntuneConnectorForm extends ModelForm<MicrosoftIntuneConnector, string> {
    protected endpoints = {
        load: (connectorUuid: string) =>
            aki(EndpointsApi).endpointsMicrosoftIntuneConnectorsRetrieve({
                connectorUuid,
            }),
        create: (data: MicrosoftIntuneConnector) =>
            aki(EndpointsApi).endpointsMicrosoftIntuneConnectorsCreate({
                microsoftIntuneConnectorRequest: data as unknown as MicrosoftIntuneConnectorRequest,
            }),
        update: (
            connectorUuid: string,
            patchedMicrosoftIntuneConnectorRequest: MicrosoftIntuneConnector,
        ) =>
            aki(EndpointsApi).endpointsMicrosoftIntuneConnectorsPartialUpdate({
                connectorUuid,
                patchedMicrosoftIntuneConnectorRequest,
            }),
    };

    public override getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated Microsoft Intune connector.")
            : msg("Successfully created Microsoft Intune connector.");
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
            <ak-form-group label=${msg("Microsoft Intune settings")} open>
                <div class="pf-c-form">
                    <ak-text-input
                        name="clientId"
                        label=${msg("Client ID")}
                        value=${this.instance?.clientId ?? ""}
                        required
                        input-hint="code"
                        help=${msg("Client ID for the app registration.")}
                    ></ak-text-input>
                    <ak-secret-text-input
                        name="clientSecret"
                        label=${msg("Client Secret")}
                        input-hint="code"
                        ?required=${!this.instance}
                        ?revealed=${!this.instance}
                        .help=${msg("Client secret for the app registration.")}
                    ></ak-secret-text-input>
                    <ak-text-input
                        name="tenantId"
                        label=${msg("Tenant ID")}
                        value=${this.instance?.tenantId ?? ""}
                        required
                        input-hint="code"
                        help=${msg("ID of the tenant.")}
                    ></ak-text-input>
                    <ak-form-element-horizontal
                        label=${msg("Certificate authorities")}
                        name="certificateAuthorities"
                    >
                        <ak-dual-select-dynamic-selected
                            .provider=${certificateProvider}
                            .selector=${certificateSelector(this.instance?.certificateAuthorities)}
                            available-label=${msg("Available Certificates")}
                            selected-label=${msg("Selected Certificates")}
                        ></ak-dual-select-dynamic-selected>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Certificate authorities which issue device certificates via Intune (Cloud PKI, SCEP or PKCS profiles), used by the endpoint stage to validate certificates. If none are selected, the client certificates configured on the brand are used.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-connector-microsoft-intune-form": MicrosoftIntuneConnectorForm;
    }
}

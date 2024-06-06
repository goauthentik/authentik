import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/components/ak-radio-input";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import YAML from "yaml";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    AuthModeEnum,
    Endpoint,
    PaginatedRACPropertyMappingList,
    PropertymappingsApi,
    ProtocolEnum,
    RacApi,
} from "@goauthentik/api";

@customElement("ak-rac-endpoint-form")
export class EndpointForm extends ModelForm<Endpoint, string> {
    @property({ type: Number })
    providerID?: number;

    propertyMappings?: PaginatedRACPropertyMappingList;

    async load(): Promise<void> {
        this.propertyMappings = await new PropertymappingsApi(
            DEFAULT_CONFIG,
        ).propertymappingsRacList({
            ordering: "name",
        });
    }

    loadInstance(pk: string): Promise<Endpoint> {
        return new RacApi(DEFAULT_CONFIG).racEndpointsRetrieve({
            pbmUuid: pk,
        });
    }

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated endpoint.")
            : msg("Successfully created endpoint.");
    }

    async send(data: Endpoint): Promise<Endpoint> {
        data.authMode = AuthModeEnum.Prompt;
        if (!this.instance) {
            data.provider = this.providerID || 0;
        } else {
            data.provider = this.instance.provider;
        }
        if (this.instance) {
            return new RacApi(DEFAULT_CONFIG).racEndpointsPartialUpdate({
                pbmUuid: this.instance.pk || "",
                patchedEndpointRequest: data,
            });
        } else {
            return new RacApi(DEFAULT_CONFIG).racEndpointsCreate({
                endpointRequest: data,
            });
        }
    }

    renderForm(): TemplateResult {
        return html`
            <ak-form-element-horizontal label=${msg("Name")} name="name" ?required=${true}>
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Protocol")} ?required=${true} name="protocol">
                <ak-radio
                    .options=${[
                        {
                            label: msg("RDP"),
                            value: ProtocolEnum.Rdp,
                        },
                        {
                            label: msg("SSH"),
                            value: ProtocolEnum.Ssh,
                        },
                        {
                            label: msg("VNC"),
                            value: ProtocolEnum.Vnc,
                        },
                    ]}
                    .value=${this.instance?.protocol}
                >
                </ak-radio>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Host")} name="host" ?required=${true}>
                <input
                    type="text"
                    value="${ifDefined(this.instance?.host)}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">${msg("Hostname/IP to connect to.")}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Maximum concurrent connections")}
                name="maximumConnections"
                ?required=${true}
            >
                <input
                    type="number"
                    value="${first(this.instance?.maximumConnections, 1)}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Maximum concurrent allowed connections to this endpoint. Can be set to -1 to disable the limit.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Property mappings")} name="propertyMappings">
                <select class="pf-c-form-control" multiple>
                    ${this.propertyMappings?.results.map((mapping) => {
                        let selected = false;
                        if (this.instance?.propertyMappings) {
                            selected = Array.from(this.instance?.propertyMappings).some((su) => {
                                return su == mapping.pk;
                            });
                        }
                        return html`<option value=${ifDefined(mapping.pk)} ?selected=${selected}>
                            ${mapping.name}
                        </option>`;
                    })}
                </select>
                <p class="pf-c-form__helper-text">
                    ${msg("Hold control/command to select multiple items.")}
                </p>
            </ak-form-element-horizontal>
            <ak-form-group>
                <span slot="header"> ${msg("Advanced settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal label=${msg("Settings")} name="settings">
                        <ak-codemirror
                            mode="yaml"
                            value="${YAML.stringify(first(this.instance?.settings, {}))}"
                        >
                        </ak-codemirror>
                        <p class="pf-c-form__helper-text">${msg("Connection settings.")}</p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        `;
    }
}

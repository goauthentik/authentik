import "#components/ak-radio-input";
import "#elements/CodeMirror";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";

import { propertyMappingsProvider, propertyMappingsSelector } from "./RACProviderFormHelpers.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { ModelForm } from "#elements/forms/ModelForm";

import { Endpoint, EndpointAuthModeEnum, ProtocolEnum, RacApi } from "@goauthentik/api";

import YAML from "yaml";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-rac-endpoint-form")
export class EndpointForm extends ModelForm<Endpoint, string> {
    @property({ type: Number })
    providerID?: number;

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
        data.authMode = EndpointAuthModeEnum.Prompt;
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
        }
        return new RacApi(DEFAULT_CONFIG).racEndpointsCreate({
            endpointRequest: data,
        });
    }

    protected override renderForm(): TemplateResult {
        return html`
            <ak-form-element-horizontal label=${msg("Provider Name")} name="name" required>
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                    placeholder=${msg("Type a provider name...")}
                    spellcheck="false"
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Protocol")} required name="protocol">
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
            <ak-form-element-horizontal label=${msg("Host")} name="host" required>
                <input
                    type="text"
                    value="${ifDefined(this.instance?.host)}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${msg("Hostname/IP to connect to. Optionally specify the port.")}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Maximum concurrent connections")}
                name="maximumConnections"
                required
            >
                <input
                    type="number"
                    value="${this.instance?.maximumConnections ?? 1}"
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
                <ak-dual-select-dynamic-selected
                    .provider=${propertyMappingsProvider}
                    .selector=${propertyMappingsSelector(this.instance?.propertyMappings)}
                    available-label="${msg("Available User Property Mappings")}"
                    selected-label="${msg("Selected User Property Mappings")}"
                ></ak-dual-select-dynamic-selected>
            </ak-form-element-horizontal>
            <ak-form-group label="${msg("Advanced settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal label=${msg("Settings")} name="settings">
                        <ak-codemirror
                            mode="yaml"
                            value="${YAML.stringify(this.instance?.settings ?? {})}"
                        >
                        </ak-codemirror>
                        <p class="pf-c-form__helper-text">${msg("Connection settings.")}</p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-rac-endpoint-form": EndpointForm;
    }
}

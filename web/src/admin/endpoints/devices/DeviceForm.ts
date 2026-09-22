import "#components/ak-text-input";
import "#components/ak-radio-input";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/FormGroup";
import "#elements/utils/TimeDeltaHelp";
import "#admin/endpoints/ak-endpoints-device-group-search";
import "#elements/CodeMirror";
import { aki } from "#common/api/client";

import { ModelForm } from "#elements/forms/ModelForm";

import { EndpointDevice, EndpointsApi, ProtocolEnum } from "@goauthentik/api";

import YAML from "yaml";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-endpoints-device-form")
export class EndpointDeviceForm extends ModelForm<EndpointDevice, string> {
    public static override verboseName = msg("Device");
    public static override verboseNamePlural = msg("Devices");
    loadInstance(pk: string): Promise<EndpointDevice> {
        return aki(EndpointsApi).endpointsDevicesRetrieve({
            deviceUuid: pk,
        });
    }

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated device.")
            : msg("Successfully created device.");
    }

    async send(data: EndpointDevice): Promise<EndpointDevice> {
        if (!this.instance) {
            return aki(EndpointsApi).endpointsDevicesCreate({
                endpointDeviceRequest: data,
            });
        }

        return aki(EndpointsApi).endpointsDevicesPartialUpdate({
            deviceUuid: this.instance.deviceUuid!,
            patchedEndpointDeviceRequest: data,
        });
    }

    renderForm() {
        return html`<ak-text-input
                name="name"
                placeholder=${msg("Device name...")}
                label=${msg("Device name")}
                value=${ifDefined(this.instance?.name)}
                required
            ></ak-text-input>
            <ak-text-input
                name="rac.host"
                placeholder=${msg("e.g. myserver.example.com, 10.0.0.1:22")}
                label=${msg("Host")}
                value=${ifDefined(this.instance?.rac?.host)}
                input-hint="code"
                ?required=${!this.instance}
                help=${msg(
                    "Hostname/IP to connect to. Optionally specify the port. Devices which are enrolled through a connector report this themselves.",
                )}
            ></ak-text-input>
            <ak-radio-input
                label=${msg("Protocol")}
                name="rac.protocol"
                ?required=${!this.instance}
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
                .value=${this.instance?.rac?.protocol}
            >
            </ak-radio-input>
            <ak-form-element-horizontal label=${msg("Device Group")} name="accessGroup">
                <ak-endpoints-device-group-search
                    .group=${this.instance?.accessGroup}
                ></ak-endpoints-device-group-search>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Attributes")} name="attributes">
                <ak-codemirror
                    mode="yaml"
                    value="${YAML.stringify(this.instance?.attributes ?? {})}"
                >
                </ak-codemirror>
                <p class="pf-c-form__helper-text">
                    ${msg("Set custom attributes using YAML or JSON.")}
                </p>
            </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-device-form": EndpointDeviceForm;
    }
}

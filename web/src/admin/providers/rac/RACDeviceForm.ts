import "#components/ak-radio-input";
import "#components/ak-text-input";
import "#components/ak-number-input";
import "#elements/CodeMirror";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import { aki } from "#common/api/client";

import { ModelForm } from "#elements/forms/ModelForm";
import { SlottedTemplateResult } from "#elements/types";

import { EndpointDevice, EndpointsApi, ProtocolEnum, RACProvider } from "@goauthentik/api";

import YAML from "yaml";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

/**
 * Key in a device's attributes under which RAC overrides are stored.
 *
 * Keep in sync with `authentik.providers.rac.models.RAC_ATTRIBUTES`.
 */
export const RAC_ATTRIBUTES = "goauthentik.io/rac";

export interface RACDeviceOverrides {
    host?: string;
    port?: number;
    protocol?: string;
    maximum_connections?: number;
    settings?: Record<string, unknown>;
    property_mappings?: string[];
}

export function racOverrides(device?: EndpointDevice | null): RACDeviceOverrides {
    const attributes = (device?.attributes ?? {}) as Record<string, unknown>;

    return (attributes[RAC_ATTRIBUTES] ?? {}) as RACDeviceOverrides;
}

interface RACDeviceFormData {
    name: string;
    host?: string;
    protocol?: string;
    maximumConnections?: number;
    settings?: Record<string, unknown>;
}

/**
 * Devices are owned by the endpoints app; this form only edits the RAC-specific
 * overrides stored in a device's attributes, so that other attributes are preserved.
 */
@customElement("ak-rac-device-form")
export class RACDeviceForm extends ModelForm<EndpointDevice, string> {
    public static override verboseName = msg("Device");
    public static override verboseNamePlural = msg("Devices");

    @property({ attribute: false })
    public provider: RACProvider | null = null;

    protected override loadInstance(pk: string): Promise<EndpointDevice> {
        return aki(EndpointsApi).endpointsDevicesRetrieve({
            deviceUuid: pk,
        });
    }

    public override getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated device.")
            : msg("Successfully created device.");
    }

    public override async send(data: RACDeviceFormData): Promise<EndpointDevice> {
        const overrides: RACDeviceOverrides = {
            ...racOverrides(this.instance),
            host: data.host || undefined,
            protocol: data.protocol || undefined,
            maximum_connections: data.maximumConnections ?? undefined,
            settings: data.settings,
        };

        const attributes = {
            ...((this.instance?.attributes ?? {}) as Record<string, unknown>),
            [RAC_ATTRIBUTES]: overrides,
        };

        if (this.instance) {
            return aki(EndpointsApi).endpointsDevicesPartialUpdate({
                deviceUuid: this.instance.deviceUuid!,
                patchedEndpointDeviceRequest: {
                    name: data.name,
                    attributes,
                },
            });
        }

        return aki(EndpointsApi).endpointsDevicesCreate({
            endpointDeviceRequest: {
                name: data.name,
                accessGroup: this.provider?.accessGroup,
                attributes,
            },
        });
    }

    protected override renderForm(): SlottedTemplateResult {
        const overrides = racOverrides(this.instance);

        return html`<ak-text-input
                label=${msg("Device Name")}
                name="name"
                required
                value="${ifDefined(this.instance?.name)}"
                placeholder=${msg("Type a name for this device...")}
                spellcheck="false"
                ?autofocus=${!this.instance}
            >
            </ak-text-input>
            <ak-text-input
                label=${msg("Host")}
                name="host"
                value="${ifDefined(overrides.host)}"
                input-hint="code"
                help=${msg(
                    "Hostname/IP to connect to, optionally with a port. Leave empty to use the address the device reports.",
                )}
                placeholder=${msg("e.g. myserver.example.com, 10.0.0.1:22")}
            >
            </ak-text-input>
            <ak-radio-input
                label=${msg("Protocol")}
                name="protocol"
                .options=${[
                    {
                        label: msg("Automatic"),
                        value: "",
                        description: html`${msg(
                            "Use the provider's protocol, or pick one based on the device's operating system.",
                        )}`,
                    },
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
                .value=${overrides.protocol ?? ""}
            >
            </ak-radio-input>
            <ak-form-group label="${msg("Advanced settings")}">
                <div class="pf-c-form">
                    <ak-number-input
                        label=${msg("Maximum concurrent connections")}
                        name="maximumConnections"
                        value="${ifDefined(overrides.maximum_connections)}"
                        help=${msg(
                            "Maximum concurrent allowed connections to this device. Can be set to -1 to disable the limit. Leave empty to use the provider's limit.",
                        )}
                    >
                    </ak-number-input>
                    <ak-form-element-horizontal label=${msg("Settings")} name="settings">
                        <ak-codemirror
                            mode="yaml"
                            value="${YAML.stringify(overrides.settings ?? {})}"
                        >
                        </ak-codemirror>
                        <p class="pf-c-form__helper-text">${msg("Connection settings.")}</p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group> `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-rac-device-form": RACDeviceForm;
    }
}

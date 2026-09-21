import "#components/ak-radio-input";
import "#components/ak-text-input";
import "#elements/forms/HorizontalFormElement";
import { aki } from "#common/api/client";

import { ModelForm } from "#elements/forms/ModelForm";
import { SlottedTemplateResult } from "#elements/types";

import {
    ProtocolEnum,
    RacApi,
    RACConnectionOverride,
    RACConnectionOverrideRequest,
    RACProvider,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

/**
 * Devices are owned by the endpoints app. This form adds the ones which are not
 * enrolled through a connector, by creating the override which says how to reach them.
 */
@customElement("ak-rac-device-form")
export class RACDeviceForm extends ModelForm<RACConnectionOverride, number> {
    public static override verboseName = msg("Device");
    public static override verboseNamePlural = msg("Devices");

    @property({ attribute: false })
    public provider: RACProvider | null = null;

    /**
     * Device to create the override for, when it already exists because it was enrolled
     * through a connector.
     */
    @property({ type: String })
    public device: string | null = null;

    protected override loadInstance(pk: number): Promise<RACConnectionOverride> {
        return aki(RacApi).racConnectionOverridesRetrieve({ id: pk });
    }

    public override getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated device.")
            : msg("Successfully created device.");
    }

    public override async send(data: RACConnectionOverrideRequest): Promise<RACConnectionOverride> {
        if (this.instance) {
            return aki(RacApi).racConnectionOverridesPartialUpdate({
                id: this.instance.pk!,
                patchedRACConnectionOverrideRequest: data,
            });
        }

        return aki(RacApi).racConnectionOverridesCreate({
            rACConnectionOverrideRequest: {
                ...data,
                device: this.device ?? undefined,
                accessGroup: this.provider?.accessGroup ?? undefined,
            },
        });
    }

    protected override renderForm(): SlottedTemplateResult {
        return html`${
                this.device
                    ? html``
                    : html`<ak-text-input
                          label=${msg("Device Name")}
                          name="deviceName"
                          required
                          value="${ifDefined(this.instance?.name)}"
                          placeholder=${msg("Type a name for this device...")}
                          spellcheck="false"
                          ?autofocus=${!this.instance}
                      >
                      </ak-text-input>`
            }
            <ak-text-input
                label=${msg("Host")}
                name="host"
                required
                value="${ifDefined(this.instance?.host)}"
                input-hint="code"
                help=${msg("Hostname/IP to connect to. Optionally specify the port.")}
                placeholder=${msg("e.g. myserver.example.com, 10.0.0.1:22")}
            >
            </ak-text-input>
            <ak-radio-input
                label=${msg("Protocol")}
                name="protocol"
                required
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
            </ak-radio-input>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-rac-device-form": RACDeviceForm;
    }
}

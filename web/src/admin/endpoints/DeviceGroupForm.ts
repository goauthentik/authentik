import "#components/ak-text-input";
import "#elements/forms/HorizontalFormElement";

import { DEFAULT_CONFIG } from "#common/api/config";

import { ModelForm } from "#elements/forms/ModelForm";
import { WithBrandConfig } from "#elements/mixins/branding";

import { DeviceGroup, DeviceGroupRequest, EndpointsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-endpoints-device-groups-form")
export class DeviceGroupForm extends WithBrandConfig(ModelForm<DeviceGroup, string>) {
    loadInstance(pk: string): Promise<DeviceGroup> {
        return new EndpointsApi(DEFAULT_CONFIG).endpointsDeviceGroupsRetrieve({
            pbmUuid: pk,
        });
    }

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated group.")
            : msg("Successfully created group.");
    }

    async send(data: DeviceGroup): Promise<DeviceGroup> {
        if (this.instance) {
            return new EndpointsApi(DEFAULT_CONFIG).endpointsDeviceGroupsPartialUpdate({
                pbmUuid: this.instance.pbmUuid,
                patchedDeviceGroupRequest: data,
            });
        }
        return new EndpointsApi(DEFAULT_CONFIG).endpointsDeviceGroupsCreate({
            deviceGroupRequest: data as unknown as DeviceGroupRequest,
        });
    }

    renderForm() {
        return html`<ak-text-input
            name="name"
            placeholder=${msg("Group name...")}
            label=${msg("Group name")}
            value=${ifDefined(this.instance?.name)}
            required
        ></ak-text-input>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-device-groups-form": DeviceGroupForm;
    }
}

import "#components/ak-text-input";
import "#elements/forms/HorizontalFormElement";

import { DEFAULT_CONFIG } from "#common/api/config";

import { ModelForm } from "#elements/forms/ModelForm";
import { WithBrandConfig } from "#elements/mixins/branding";

import { DeviceTag, DeviceTagRequest, EndpointsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-endpoints-device-tags-form")
export class DeviceTagForm extends WithBrandConfig(ModelForm<DeviceTag, string>) {
    loadInstance(pk: string): Promise<DeviceTag> {
        return new EndpointsApi(DEFAULT_CONFIG).endpointsDeviceTagsRetrieve({
            pbmUuid: pk,
        });
    }

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated group.")
            : msg("Successfully created group.");
    }

    async send(data: DeviceTag): Promise<DeviceTag> {
        if (this.instance) {
            return new EndpointsApi(DEFAULT_CONFIG).endpointsDeviceTagsPartialUpdate({
                pbmUuid: this.instance.pbmUuid,
                patchedDeviceTagRequest: data,
            });
        }
        return new EndpointsApi(DEFAULT_CONFIG).endpointsDeviceTagsCreate({
            deviceTagRequest: data as unknown as DeviceTagRequest,
        });
    }

    renderForm() {
        return html`<ak-text-input
            name="name"
            placeholder=${msg("Tag name...")}
            label=${msg("Tag name")}
            value=${ifDefined(this.instance?.name)}
            required
        ></ak-text-input>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-device-tags-form": DeviceTagForm;
    }
}

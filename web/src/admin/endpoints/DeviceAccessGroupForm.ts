import "#components/ak-text-input";
import "#elements/forms/HorizontalFormElement";

import { DEFAULT_CONFIG } from "#common/api/config";
import { PFSize } from "#common/enums";

import { ModelForm } from "#elements/forms/ModelForm";
import { WithBrandConfig } from "#elements/mixins/branding";

import { DeviceAccessGroup, DeviceAccessGroupRequest, EndpointsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

/**
 * Device Access Group Form
 *
 * @prop {string} instancePk - The primary key of the instance to load.
 */
@customElement("ak-endpoints-device-access-groups-form")
export class DeviceAccessGroupForm extends WithBrandConfig(ModelForm<DeviceAccessGroup, string>) {
    public static override verboseName = msg("Device Access Group");
    public static override verboseNamePlural = msg("Device Access Groups");

    public override size = PFSize.Small;

    protected override loadInstance(pk: string): Promise<DeviceAccessGroup> {
        return new EndpointsApi(DEFAULT_CONFIG).endpointsDeviceAccessGroupsRetrieve({
            pbmUuid: pk,
        });
    }

    public override getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated group.")
            : msg("Successfully created group.");
    }

    protected override async send(data: DeviceAccessGroup): Promise<DeviceAccessGroup> {
        if (this.instance) {
            return new EndpointsApi(DEFAULT_CONFIG).endpointsDeviceAccessGroupsPartialUpdate({
                pbmUuid: this.instance.pbmUuid,
                patchedDeviceAccessGroupRequest: data,
            });
        }

        return new EndpointsApi(DEFAULT_CONFIG).endpointsDeviceAccessGroupsCreate({
            deviceAccessGroupRequest: data as unknown as DeviceAccessGroupRequest,
        });
    }

    protected override renderForm() {
        return html`<ak-text-input
            name="name"
            autocomplete="off"
            placeholder=${msg("Type a group name...")}
            label=${msg("Group Name")}
            value=${ifDefined(this.instance?.name)}
            required
        ></ak-text-input>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-device-access-groups-form": DeviceAccessGroupForm;
    }
}

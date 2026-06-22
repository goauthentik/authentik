import "#components/ak-text-input";
import "#elements/forms/HorizontalFormElement";

import { aki } from "#common/api/client";
import { PFSize } from "#common/enums";

import { WithBrandConfig } from "#elements/mixins/branding";

import { ObjectAttributeModelForm } from "#admin/object-attributes/renderAttributes";

import {
    DeviceAccessGroup,
    DeviceAccessGroupRequest,
    EndpointsApi,
    ModelEnum,
} from "@goauthentik/api";

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
export class DeviceAccessGroupForm extends WithBrandConfig(
    ObjectAttributeModelForm<DeviceAccessGroup, string>,
) {
    public model = ModelEnum.AuthentikEndpointsDeviceaccessgroup;

    public static override verboseName = msg("Device Access Group");
    public static override verboseNamePlural = msg("Device Access Groups");

    public override size = PFSize.Small;

    protected override loadInstance(pk: string): Promise<DeviceAccessGroup> {
        return aki(EndpointsApi).endpointsDeviceAccessGroupsRetrieve({
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
            return aki(EndpointsApi).endpointsDeviceAccessGroupsPartialUpdate({
                pbmUuid: this.instance.pbmUuid,
                patchedDeviceAccessGroupRequest: data,
            });
        }

        return aki(EndpointsApi).endpointsDeviceAccessGroupsCreate({
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
            ></ak-text-input>
            ${this.renderObjectAttributes(this.objAttributes, this.instance)}`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-device-access-groups-form": DeviceAccessGroupForm;
    }
}

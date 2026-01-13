import "#admin/groups/GroupForm";
import "#admin/rbac/ObjectPermissionModal";
import "#admin/users/UserForm";
import "#components/ak-status-label";
import "#elements/forms/ModalForm";
import "#elements/forms/ProxyForm";
import "#admin/endpoints/devices/DeviceUserBindingForm";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { BoundPoliciesList } from "#admin/policies/BoundPoliciesList";
import { PolicyBindingCheckTarget, PolicyBindingCheckTargetToLabel } from "#admin/policies/utils";

import { DeviceUserBinding, EndpointsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-bound-device-users-list")
export class BoundDeviceUsersList extends BoundPoliciesList<DeviceUserBinding> {
    async apiEndpoint(): Promise<PaginatedResponse<DeviceUserBinding>> {
        return new EndpointsApi(DEFAULT_CONFIG).endpointsDeviceBindingsList({
            ...(await this.defaultEndpointConfig()),
            target: this.target || "",
        });
    }

    protected override rowLabel(item: DeviceUserBinding): string | null {
        return item.order?.toString() ?? null;
    }

    protected bindingEditForm: string = "ak-device-binding-form";

    protected columns: TableColumn[] = [
        [
            [PolicyBindingCheckTarget.user, PolicyBindingCheckTarget.group]
                .map((ct) => PolicyBindingCheckTargetToLabel(ct))
                .join(" / "),
        ],
        [msg("Primary")],
    ];

    row(item: DeviceUserBinding): SlottedTemplateResult[] {
        return [
            html`${this.getPolicyUserGroupRow(item)}`,
            html`<ak-status-label ?good=${item.isPrimary}></ak-status-label>`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-bound-device-users-list": BoundDeviceUsersList;
    }
}

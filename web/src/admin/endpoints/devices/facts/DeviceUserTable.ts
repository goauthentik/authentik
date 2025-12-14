import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { trySortNumerical } from "#admin/endpoints/devices/utils";

import { DeviceUser, EndpointDeviceDetails } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-endpoints-device-users-table")
export class DeviceUserTable extends Table<DeviceUser> {
    @property({ attribute: false })
    device?: EndpointDeviceDetails;

    protected async apiEndpoint(): Promise<PaginatedResponse<DeviceUser>> {
        const items = (this.device?.facts.data.users || []).sort(trySortNumerical);
        return {
            pagination: {
                count: items.length,
                current: 1,
                totalPages: 1,
                startIndex: 1,
                endIndex: items.length,
                next: 0,
                previous: 0,
            },
            results: items,
        };
    }
    protected columns: TableColumn[] = [
        [msg("ID")],
        [msg("Username")],
        [msg("Name")],
        [msg("Home directory")],
    ];
    protected row(item: DeviceUser): SlottedTemplateResult[] {
        return [
            html`${item.id}`,
            html`${item.username}`,
            html`${item.name ?? "-"}`,
            html`${item.home ?? "-"}`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-device-users-table": DeviceUserTable;
    }
}

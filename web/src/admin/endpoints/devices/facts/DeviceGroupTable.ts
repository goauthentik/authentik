import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { trySortNumerical } from "#admin/endpoints/devices/utils";

import { DeviceGroup, EndpointDeviceDetails } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-endpoints-device-groups-table")
export class DeviceGroupTable extends Table<DeviceGroup> {
    @property({ attribute: false })
    device?: EndpointDeviceDetails;

    protected async apiEndpoint(): Promise<PaginatedResponse<DeviceGroup>> {
        const items = (this.device?.facts.data.groups || []).sort(trySortNumerical);
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
    protected columns: TableColumn[] = [[msg("ID")], [msg("Name")]];
    protected row(item: DeviceGroup): SlottedTemplateResult[] {
        return [html`${item.id}`, html`${item.name ?? "-"}`];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-device-groups-table": DeviceGroupTable;
    }
}

import { groupBy, GroupResult } from "#common/utils";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { EndpointDeviceDetails, Software } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-endpoints-device-software-table")
export class DeviceSoftwareTable extends Table<Software> {
    @property({ attribute: false })
    device?: EndpointDeviceDetails;

    protected async apiEndpoint(): Promise<PaginatedResponse<Software>> {
        const items = (this.device?.facts.data.software || []).sort((a, b) =>
            a.name.localeCompare(b.name),
        );
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

    protected groupBy(items: Software[]): GroupResult<Software>[] {
        return groupBy(items, (item) => item.source);
    }

    protected columns: TableColumn[] = [
        [msg("Name")],
        [msg("Version")],
        [msg("Source")],
        [msg("Path")],
    ];
    protected row(item: Software): SlottedTemplateResult[] {
        return [
            html`${item.name}`,
            html`${item.version ?? "-"}`,
            html`${item.source}`,
            html`${item.path ?? "-"}`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-device-software-table": DeviceSoftwareTable;
    }
}

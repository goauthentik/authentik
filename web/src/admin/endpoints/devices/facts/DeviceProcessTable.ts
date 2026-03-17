import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { trySortNumerical } from "#admin/endpoints/devices/utils";

import { EndpointDeviceDetails, Process } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-endpoints-device-process-table")
export class DeviceProcessTable extends Table<Process> {
    @property({ attribute: false })
    device?: EndpointDeviceDetails;

    protected async apiEndpoint(): Promise<PaginatedResponse<Process>> {
        const items = (this.device?.facts.data.processes || []).sort(trySortNumerical);
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
    protected columns: TableColumn[] = [[msg("ID")], [msg("Name")], [msg("User")]];
    protected row(item: Process): SlottedTemplateResult[] {
        return [html`${item.id}`, html`${item.name}`, html`${item.user ?? "-"}`];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-device-process-table": DeviceProcessTable;
    }
}

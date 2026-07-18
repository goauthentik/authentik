import { groupBy, GroupResult } from "#common/utils";

import { StaticTable } from "#elements/table/StaticTable";
import { TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { Software } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-endpoints-device-software-table")
export class DeviceSoftwareTable extends StaticTable<Software> {
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

import { StaticTable } from "#elements/table/StaticTable";
import { TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { DeviceGroup } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-endpoints-device-groups-table")
export class DeviceGroupTable extends StaticTable<DeviceGroup> {
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

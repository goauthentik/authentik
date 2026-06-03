import { StaticTable } from "#elements/table/StaticTable";
import { TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { Process } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-endpoints-device-process-table")
export class DeviceProcessTable extends StaticTable<Process> {
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

import { StaticTable } from "#elements/table/StaticTable";
import { TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { DeviceUser } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-endpoints-device-users-table")
export class DeviceUserTable extends StaticTable<DeviceUser> {
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

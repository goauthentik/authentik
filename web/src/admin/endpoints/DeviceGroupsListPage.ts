import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { DeviceGroup, EndpointsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-endpoints-device-groups-list")
export class DeviceGroupsListPage extends TablePage<DeviceGroup> {
    public pageIcon = "pf-icon pf-icon-server-group	";
    public pageTitle = msg("Device groups");
    public pageDescription = msg("TODO");

    protected columns: TableColumn[] = [[msg("Name"), "name"]];

    async apiEndpoint(): Promise<PaginatedResponse<DeviceGroup>> {
        return new EndpointsApi(DEFAULT_CONFIG).endpointsDeviceGroupsList(
            await this.defaultEndpointConfig(),
        );
    }

    row(item: DeviceGroup): SlottedTemplateResult[] {
        return [html`${item.name}`];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-device-groups-list": DeviceGroupsListPage;
    }
}

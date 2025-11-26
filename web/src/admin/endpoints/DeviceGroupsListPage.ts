import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#admin/endpoints/DeviceGroupForm";
import "#admin/policies/BoundPoliciesList";

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
    public pageDescription = msg("Create groups of devices to manage access.");

    protected searchEnabled: boolean = true;
    protected columns: TableColumn[] = [
        [msg("Name"), "name"],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    checkbox = true;
    expandable = true;

    async apiEndpoint(): Promise<PaginatedResponse<DeviceGroup>> {
        return new EndpointsApi(DEFAULT_CONFIG).endpointsDeviceGroupsList(
            await this.defaultEndpointConfig(),
        );
    }

    row(item: DeviceGroup): SlottedTemplateResult[] {
        return [
            html`${item.name}`,
            html`<ak-forms-modal>
                <span slot="submit">${msg("Update")}</span>
                <span slot="header">${msg("Update Group")}</span>
                <ak-endpoints-device-groups-form slot="form" pk=${item.pbmUuid}>
                </ak-endpoints-device-groups-form>
                <button slot="trigger" class="pf-c-button pf-m-plain">
                    <pf-tooltip position="top" content=${msg("Edit")}>
                        <i class="fas fa-edit" aria-hidden="true"></i>
                    </pf-tooltip>
                </button>
            </ak-forms-modal>`,
        ];
    }

    renderExpanded(item: DeviceGroup) {
        return html`<div class="pf-c-content">
            <ak-bound-policies-list .target=${item.pbmUuid}></ak-bound-policies-list>
        </div>`;
    }

    renderObjectCreate() {
        return html`<ak-forms-modal>
            <span slot="submit">${msg("Create")}</span>
            <span slot="header">${msg("Create Device Group")}</span>
            <ak-endpoints-device-groups-form slot="form"></ak-endpoints-device-groups-form>
            <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Create")}</button>
        </ak-forms-modal>`;
    }

    renderToolbarSelected() {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Device Group(s)")}
            .objects=${this.selectedElements}
            .metadata=${(item: DeviceGroup) => {
                return [{ key: msg("Name"), value: item.name }];
            }}
            .usedBy=${(item: DeviceGroup) => {
                return new EndpointsApi(DEFAULT_CONFIG).endpointsDeviceGroupsUsedByList({
                    pbmUuid: item.pbmUuid,
                });
            }}
            .delete=${(item: DeviceGroup) => {
                return new EndpointsApi(DEFAULT_CONFIG).endpointsDeviceGroupsDestroy({
                    pbmUuid: item.pbmUuid,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-device-groups-list": DeviceGroupsListPage;
    }
}

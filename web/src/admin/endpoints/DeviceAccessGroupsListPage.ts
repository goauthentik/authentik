import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#admin/endpoints/DeviceAccessGroupForm";
import "#admin/policies/BoundPoliciesList";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { DeviceAccessGroup, EndpointsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-endpoints-device-access-groups-list")
export class DeviceAccessGroupsListPage extends TablePage<DeviceAccessGroup> {
    public pageIcon = "pf-icon pf-icon-server-group	";
    public pageTitle = msg("Device access groups");
    public pageDescription = msg("Create groups of devices to manage access.");

    protected searchEnabled: boolean = true;
    protected columns: TableColumn[] = [
        [msg("Name"), "name"],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    checkbox = true;
    expandable = true;

    async apiEndpoint(): Promise<PaginatedResponse<DeviceAccessGroup>> {
        return new EndpointsApi(DEFAULT_CONFIG).endpointsDeviceAccessGroupsList(
            await this.defaultEndpointConfig(),
        );
    }

    row(item: DeviceAccessGroup): SlottedTemplateResult[] {
        return [
            html`${item.name}`,
            html`<div>
                <ak-forms-modal>
                    <span slot="submit">${msg("Update")}</span>
                    <span slot="header">${msg("Update Group")}</span>
                    <ak-endpoints-device-access-groups-form slot="form" .instancePk=${item.pbmUuid}>
                    </ak-endpoints-device-access-groups-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <pf-tooltip position="top" content=${msg("Edit")}>
                            <i class="fas fa-edit" aria-hidden="true"></i>
                        </pf-tooltip>
                    </button>
                </ak-forms-modal>
            </div>`,
        ];
    }

    renderExpanded(item: DeviceAccessGroup) {
        return html`<div class="pf-c-content">
            <ak-bound-policies-list .target=${item.pbmUuid}></ak-bound-policies-list>
        </div>`;
    }

    renderObjectCreate() {
        return html`<ak-forms-modal>
            <span slot="submit">${msg("Create")}</span>
            <span slot="header">${msg("Create Device Group")}</span>
            <ak-endpoints-device-access-groups-form
                slot="form"
            ></ak-endpoints-device-access-groups-form>
            <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Create")}</button>
        </ak-forms-modal>`;
    }

    renderToolbarSelected() {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            object-label=${msg("Device Group(s)")}
            .objects=${this.selectedElements}
            .metadata=${(item: DeviceAccessGroup) => {
                return [{ key: msg("Name"), value: item.name }];
            }}
            .usedBy=${(item: DeviceAccessGroup) => {
                return new EndpointsApi(DEFAULT_CONFIG).endpointsDeviceAccessGroupsUsedByList({
                    pbmUuid: item.pbmUuid,
                });
            }}
            .delete=${(item: DeviceAccessGroup) => {
                return new EndpointsApi(DEFAULT_CONFIG).endpointsDeviceAccessGroupsDestroy({
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
        "ak-endpoints-device-access-groups-list": DeviceAccessGroupsListPage;
    }
}

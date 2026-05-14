import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#admin/endpoints/DeviceAccessGroupForm";
import "#admin/policies/BoundPoliciesList";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { IconEditButton, ModalInvokerButton } from "#elements/dialogs";
import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { DeviceAccessGroupForm } from "#admin/endpoints/DeviceAccessGroupForm";

import { DeviceAccessGroup, EndpointsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-endpoints-device-access-groups-list")
export class DeviceAccessGroupsListPage extends TablePage<DeviceAccessGroup> {
    protected searchEnabled: boolean = true;
    protected columns: TableColumn[] = [
        [msg("Name"), "name"],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    public override pageIcon = "pf-icon pf-icon-server-group	";
    public override pageTitle = msg("Device access groups");
    public override pageDescription = msg("Create groups of devices to manage access.");
    public override searchPlaceholder = msg("Search device groups by name...");

    public override checkbox = true;
    public override expandable = true;

    protected override async apiEndpoint(): Promise<PaginatedResponse<DeviceAccessGroup>> {
        return new EndpointsApi(DEFAULT_CONFIG).endpointsDeviceAccessGroupsList(
            await this.defaultEndpointConfig(),
        );
    }

    protected override row(item: DeviceAccessGroup): SlottedTemplateResult[] {
        return [
            // ---
            item.name,
            html`<div class="ak-c-table__actions">
                ${IconEditButton(DeviceAccessGroupForm, item.pbmUuid)}
            </div>`,
        ];
    }

    protected override renderExpanded(item: DeviceAccessGroup) {
        return html`<div class="pf-c-content">
            <ak-bound-policies-list .target=${item.pbmUuid}></ak-bound-policies-list>
        </div>`;
    }

    protected override renderObjectCreate(): SlottedTemplateResult {
        return ModalInvokerButton(DeviceAccessGroupForm);
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

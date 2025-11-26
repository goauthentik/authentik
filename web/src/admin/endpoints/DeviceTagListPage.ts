import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#admin/endpoints/DeviceTagForm";
import "#admin/policies/BoundPoliciesList";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { DeviceTag, EndpointsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-endpoints-device-tag-list")
export class DeviceTagsListPage extends TablePage<DeviceTag> {
    public pageIcon = "fa fa-tag";
    public pageTitle = msg("Device tags");
    public pageDescription = msg("Create tags for devices.");

    protected searchEnabled: boolean = true;
    protected columns: TableColumn[] = [
        [msg("Name"), "name"],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    checkbox = true;

    async apiEndpoint(): Promise<PaginatedResponse<DeviceTag>> {
        return new EndpointsApi(DEFAULT_CONFIG).endpointsDeviceTagsList(
            await this.defaultEndpointConfig(),
        );
    }

    row(item: DeviceTag): SlottedTemplateResult[] {
        return [
            html`${item.name}`,
            html`<ak-forms-modal>
                <span slot="submit">${msg("Update")}</span>
                <span slot="header">${msg("Update Tag")}</span>
                <ak-endpoints-device-tag-form slot="form" pk=${item.pbmUuid}>
                </ak-endpoints-device-tag-form>
                <button slot="trigger" class="pf-c-button pf-m-plain">
                    <pf-tooltip position="top" content=${msg("Edit")}>
                        <i class="fas fa-edit" aria-hidden="true"></i>
                    </pf-tooltip>
                </button>
            </ak-forms-modal>`,
        ];
    }

    renderObjectCreate() {
        return html`<ak-forms-modal>
            <span slot="submit">${msg("Create")}</span>
            <span slot="header">${msg("Create Device Tag")}</span>
            <ak-endpoints-device-tags-form slot="form"></ak-endpoints-device-tags-form>
            <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Create")}</button>
        </ak-forms-modal>`;
    }

    renderToolbarSelected() {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Device Tag(s)")}
            .objects=${this.selectedElements}
            .metadata=${(item: DeviceTag) => {
                return [{ key: msg("Name"), value: item.name }];
            }}
            .usedBy=${(item: DeviceTag) => {
                return new EndpointsApi(DEFAULT_CONFIG).endpointsDeviceTagsUsedByList({
                    pbmUuid: item.pbmUuid,
                });
            }}
            .delete=${(item: DeviceTag) => {
                return new EndpointsApi(DEFAULT_CONFIG).endpointsDeviceTagsDestroy({
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
        "ak-endpoints-device-tag-list": DeviceTagsListPage;
    }
}

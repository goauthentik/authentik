import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#elements/sync/SyncObjectForm";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import {
    ProvidersApi,
    ProvidersScimSyncObjectCreateRequest,
    SCIMProviderGroup,
    SyncObjectModelEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-provider-scim-groups-list")
export class SCIMProviderGroupList extends Table<SCIMProviderGroup> {
    @property({ type: Number })
    providerId?: number;

    protected override searchEnabled = true;

    expandable = true;
    checkbox = true;
    clearOnRefresh = true;

    renderToolbar(): TemplateResult {
        return html`<ak-forms-modal cancelText=${msg("Close")} ?closeAfterSuccessfulSubmit=${false}>
                <span slot="submit">${msg("Sync")}</span>
                <span slot="header">${msg("Sync Group")}</span>
                <ak-sync-object-form
                    .provider=${this.providerId}
                    model=${SyncObjectModelEnum.AuthentikCoreModelsGroup}
                    .sync=${(data: ProvidersScimSyncObjectCreateRequest) => {
                        return new ProvidersApi(DEFAULT_CONFIG).providersScimSyncObjectCreate(data);
                    }}
                    slot="form"
                >
                </ak-sync-object-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Sync")}</button>
            </ak-forms-modal>
            ${super.renderToolbar()}`;
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("SCIM Group(s)")}
            .objects=${this.selectedElements}
            .delete=${(item: SCIMProviderGroup) => {
                return new ProvidersApi(DEFAULT_CONFIG).providersScimGroupsDestroy({
                    id: item.id,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    async apiEndpoint(): Promise<PaginatedResponse<SCIMProviderGroup>> {
        return new ProvidersApi(DEFAULT_CONFIG).providersScimGroupsList({
            ...(await this.defaultEndpointConfig()),
            providerId: this.providerId,
        });
    }

    protected override rowLabel(item: SCIMProviderGroup): string {
        return item.groupObj.name;
    }

    protected columns: TableColumn[] = [
        // ---
        [msg("Name")],
        [msg("ID")],
    ];

    row(item: SCIMProviderGroup): SlottedTemplateResult[] {
        return [
            html`<a href="#/identity/groups/${item.groupObj.pk}">
                <div>${item.groupObj.name}</div>
            </a>`,
            html`${item.id}`,
        ];
    }
    renderExpanded(item: SCIMProviderGroup): TemplateResult {
        return html`<pre>${JSON.stringify(item.attributes, null, 4)}</pre>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-scim-groups-list": SCIMProviderGroupList;
    }
}

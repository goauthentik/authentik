import { DEFAULT_CONFIG } from "@goauthentik/common/api/config.js";
import "@goauthentik/elements/forms/DeleteBulkForm";
import "@goauthentik/elements/forms/ModalForm";
import "@goauthentik/elements/sync/SyncObjectForm";
import { PaginatedResponse, Table, TableColumn } from "@goauthentik/elements/table/Table";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import {
    MicrosoftEntraProviderGroup,
    ProvidersApi,
    ProvidersMicrosoftEntraSyncObjectCreateRequest,
    SyncObjectModelEnum,
} from "@goauthentik/api";

@customElement("ak-provider-microsoft-entra-groups-list")
export class MicrosoftEntraProviderGroupList extends Table<MicrosoftEntraProviderGroup> {
    @property({ type: Number })
    providerId?: number;

    expandable = true;

    searchEnabled(): boolean {
        return true;
    }

    renderToolbar(): TemplateResult {
        return html`<ak-forms-modal cancelText=${msg("Close")} ?closeAfterSuccessfulSubmit=${false}>
                <span slot="submit">${msg("Sync")}</span>
                <span slot="header">${msg("Sync Group")}</span>
                <ak-sync-object-form
                    .provider=${this.providerId}
                    model=${SyncObjectModelEnum.AuthentikCoreModelsGroup}
                    .sync=${(data: ProvidersMicrosoftEntraSyncObjectCreateRequest) => {
                        return new ProvidersApi(
                            DEFAULT_CONFIG,
                        ).providersMicrosoftEntraSyncObjectCreate(data);
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
            objectLabel=${msg("Microsoft Entra Group(s)")}
            .objects=${this.selectedElements}
            .delete=${(item: MicrosoftEntraProviderGroup) => {
                return new ProvidersApi(DEFAULT_CONFIG).providersMicrosoftEntraGroupsDestroy({
                    id: item.id,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    async apiEndpoint(): Promise<PaginatedResponse<MicrosoftEntraProviderGroup>> {
        return new ProvidersApi(DEFAULT_CONFIG).providersMicrosoftEntraGroupsList({
            ...(await this.defaultEndpointConfig()),
            providerId: this.providerId,
        });
    }

    columns(): TableColumn[] {
        return [new TableColumn(msg("Name")), new TableColumn(msg("ID"))];
    }

    row(item: MicrosoftEntraProviderGroup): TemplateResult[] {
        return [
            html`<a href="#/identity/groups/${item.groupObj.pk}">
                <div>${item.groupObj.name}</div>
            </a>`,
            html`${item.id}`,
        ];
    }

    renderExpanded(item: MicrosoftEntraProviderGroup): TemplateResult {
        return html`<td role="cell" colspan="4">
            <div class="pf-c-table__expandable-row-content">
                <pre>${JSON.stringify(item.attributes, null, 4)}</pre>
            </div>
        </td>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-microsoft-entra-groups-list": MicrosoftEntraProviderGroupList;
    }
}

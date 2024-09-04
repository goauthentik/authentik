import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/forms/DeleteBulkForm";
import "@goauthentik/elements/forms/ModalForm";
import "@goauthentik/elements/sync/SyncObjectForm";
import { PaginatedResponse, Table, TableColumn } from "@goauthentik/elements/table/Table";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { GoogleWorkspaceProviderGroup, ProvidersApi, SyncObjectModelEnum } from "@goauthentik/api";

@customElement("ak-provider-google-workspace-groups-list")
export class GoogleWorkspaceProviderGroupList extends Table<GoogleWorkspaceProviderGroup> {
    @property({ type: Number })
    providerId?: number;

    expandable = true;

    searchEnabled(): boolean {
        return true;
    }

    checkbox = true;
    clearOnRefresh = true;

    renderToolbar(): TemplateResult {
        return html`<ak-forms-modal cancelText=${msg("Close")} ?closeAfterSuccessfulSubmit=${false}>
                <span slot="submit">${msg("Sync")}</span>
                <span slot="header">${msg("Sync Group")}</span>
                <ak-sync-object-form
                    .provider=${this.providerId}
                    model=${SyncObjectModelEnum.Group}
                    .sync=${new ProvidersApi(DEFAULT_CONFIG)
                        .providersGoogleWorkspaceSyncObjectCreate}
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
            objectLabel=${msg("Google Workspace Group(s)")}
            .objects=${this.selectedElements}
            .delete=${(item: GoogleWorkspaceProviderGroup) => {
                return new ProvidersApi(DEFAULT_CONFIG).providersGoogleWorkspaceGroupsDestroy({
                    id: item.id,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    async apiEndpoint(): Promise<PaginatedResponse<GoogleWorkspaceProviderGroup>> {
        return new ProvidersApi(DEFAULT_CONFIG).providersGoogleWorkspaceGroupsList({
            ...(await this.defaultEndpointConfig()),
            providerId: this.providerId,
        });
    }

    columns(): TableColumn[] {
        return [new TableColumn(msg("Name")), new TableColumn(msg("ID"))];
    }

    row(item: GoogleWorkspaceProviderGroup): TemplateResult[] {
        return [
            html`<a href="#/identity/groups/${item.groupObj.pk}">
                <div>${item.groupObj.name}</div>
            </a>`,
            html`${item.id}`,
        ];
    }

    renderExpanded(item: GoogleWorkspaceProviderGroup): TemplateResult {
        return html`<td role="cell" colspan="4">
            <div class="pf-c-table__expandable-row-content">
                <pre>${JSON.stringify(item.attributes, null, 4)}</pre>
            </div>
        </td>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-google-workspace-groups-list": GoogleWorkspaceProviderGroupList;
    }
}

import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { uiConfig } from "@goauthentik/common/ui/config";
import "@goauthentik/elements/forms/DeleteBulkForm";
import { PaginatedResponse, Table, TableColumn } from "@goauthentik/elements/table/Table";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { MicrosoftEntraProviderUser, ProvidersApi } from "@goauthentik/api";

@customElement("ak-provider-microsoft-entra-users-list")
export class MicrosoftEntraProviderUserList extends Table<MicrosoftEntraProviderUser> {
    @property({ type: Number })
    providerId?: number;

    expandable = true;

    searchEnabled(): boolean {
        return true;
    }

    checkbox = true;
    clearOnRefresh = true;

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Microsoft Entra User(s)")}
            .objects=${this.selectedElements}
            .delete=${(item: MicrosoftEntraProviderUser) => {
                return new ProvidersApi(DEFAULT_CONFIG).providersMicrosoftEntraUsersDestroy({
                    id: item.id,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    async apiEndpoint(page: number): Promise<PaginatedResponse<MicrosoftEntraProviderUser>> {
        return new ProvidersApi(DEFAULT_CONFIG).providersMicrosoftEntraUsersList({
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            ordering: this.order,
            search: this.search || "",
            providerId: this.providerId,
        });
    }

    columns(): TableColumn[] {
        return [new TableColumn(msg("Username")), new TableColumn(msg("ID"))];
    }

    row(item: MicrosoftEntraProviderUser): TemplateResult[] {
        return [
            html`<a href="#/identity/users/${item.userObj.pk}">
                <div>${item.userObj.username}</div>
                <small>${item.userObj.name}</small>
            </a>`,
            html`${item.id}`,
        ];
    }

    renderExpanded(item: MicrosoftEntraProviderUser): TemplateResult {
        return html`<td role="cell" colspan="4">
            <div class="pf-c-table__expandable-row-content">
                <pre>${JSON.stringify(item.attributes, null, 4)}</pre>
            </div>
        </td>`;
    }
}

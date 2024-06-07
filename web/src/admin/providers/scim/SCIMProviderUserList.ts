import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { uiConfig } from "@goauthentik/common/ui/config";
import "@goauthentik/elements/forms/DeleteBulkForm";
import { PaginatedResponse, Table, TableColumn } from "@goauthentik/elements/table/Table";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { ProvidersApi, SCIMProviderUser } from "@goauthentik/api";

@customElement("ak-provider-scim-users-list")
export class SCIMProviderUserList extends Table<SCIMProviderUser> {
    @property({ type: Number })
    providerId?: number;

    searchEnabled(): boolean {
        return true;
    }

    checkbox = true;
    clearOnRefresh = true;

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("SCIM User(s)")}
            .objects=${this.selectedElements}
            .delete=${(item: SCIMProviderUser) => {
                return new ProvidersApi(DEFAULT_CONFIG).providersScimUsersDestroy({
                    id: item.id,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    async apiEndpoint(page: number): Promise<PaginatedResponse<SCIMProviderUser>> {
        return new ProvidersApi(DEFAULT_CONFIG).providersScimUsersList({
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

    row(item: SCIMProviderUser): TemplateResult[] {
        return [
            html`<a href="#/identity/users/${item.userObj.pk}">
                <div>${item.userObj.username}</div>
                <small>${item.userObj.name}</small>
            </a>`,
            html`${item.id}`,
        ];
    }
}

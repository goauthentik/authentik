import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#elements/sync/SyncObjectForm";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import {
    ProvidersApi,
    ProvidersScimSyncObjectCreateRequest,
    SCIMProviderUser,
    SyncObjectModelEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-provider-scim-users-list")
export class SCIMProviderUserList extends Table<SCIMProviderUser> {
    @property({ type: Number })
    providerId?: number;

    protected override searchEnabled = true;

    expandable = true;
    checkbox = true;
    clearOnRefresh = true;

    renderToolbar(): TemplateResult {
        return html`<ak-forms-modal cancelText=${msg("Close")} ?closeAfterSuccessfulSubmit=${false}>
                <span slot="submit">${msg("Sync")}</span>
                <span slot="header">${msg("Sync User")}</span>
                <ak-sync-object-form
                    .provider=${this.providerId}
                    model=${SyncObjectModelEnum.AuthentikCoreModelsUser}
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

    async apiEndpoint(): Promise<PaginatedResponse<SCIMProviderUser>> {
        return new ProvidersApi(DEFAULT_CONFIG).providersScimUsersList({
            ...(await this.defaultEndpointConfig()),
            providerId: this.providerId,
        });
    }

    protected override rowLabel(item: SCIMProviderUser): string {
        return item.userObj.name || item.userObj.username;
    }

    protected columns: TableColumn[] = [
        // ---
        [msg("Username")],
        [msg("ID")],
    ];

    row(item: SCIMProviderUser): SlottedTemplateResult[] {
        return [
            html`<a href="#/identity/users/${item.userObj.pk}">
                <div>${item.userObj.username}</div>
                <small>${item.userObj.name}</small>
            </a>`,
            html`${item.id}`,
        ];
    }
    renderExpanded(item: SCIMProviderUser): TemplateResult {
        return html`<pre>${JSON.stringify(item.attributes, null, 4)}</pre>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-scim-users-list": SCIMProviderUserList;
    }
}

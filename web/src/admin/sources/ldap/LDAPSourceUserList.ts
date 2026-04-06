import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#elements/sync/SyncObjectForm";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import {
    SourcesApi,
    SourcesUserConnectionsLdapCreateRequest,
    SyncObjectModelEnum,
    UserLDAPSourceConnection,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-source-ldap-users-list")
export class LDAPSourceUserList extends Table<UserLDAPSourceConnection> {
    @property()
    sourceSlug?: string;

    protected override searchEnabled = true;

    checkbox = true;
    clearOnRefresh = true;

    renderToolbar(): TemplateResult {
        return html`<ak-forms-modal cancelText=${msg("Close")} ?closeAfterSuccessfulSubmit=${false}>
                <span slot="submit">${msg("Sync")}</span>
                <span slot="header">${msg("Sync Group")}</span>
                <ak-sync-object-form
                    .provider=${this.providerId}
                    model=${SyncObjectModelEnum.AuthentikCoreModelsGroup}
                    .sync=${(data: SourcesUserConnectionsLdapCreateRequest) => {
                        return new SourcesApi(DEFAULT_CONFIG).sourcesUserConnectionsLdapCreate(
                            data,
                        );
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
            object-label=${msg("LDAP User(s)")}
            .objects=${this.selectedElements}
            .delete=${(item: UserLDAPSourceConnection) => {
                return new SourcesApi(DEFAULT_CONFIG).sourcesUserConnectionsLdapDestroy({
                    id: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    async apiEndpoint(): Promise<PaginatedResponse<UserLDAPSourceConnection>> {
        return new SourcesApi(DEFAULT_CONFIG).sourcesUserConnectionsLdapList({
            ...(await this.defaultEndpointConfig()),
            sourceSlug: this.sourceSlug,
        });
    }

    protected override rowLabel(item: UserLDAPSourceConnection): string {
        return item.userObj.name;
    }

    protected columns: TableColumn[] = [
        // ---
        [msg("Name")],
        [msg("ID")],
    ];

    row(item: UserLDAPSourceConnection): SlottedTemplateResult[] {
        return [
            html`<a href="#/identity/users/${item.userObj.pk}">
                <div>${item.userObj.username}</div>
                <small>${item.userObj.name}</small>
            </a>`,
            html`${item.pk}`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-ldap-users-list": LDAPSourceUserList;
    }
}

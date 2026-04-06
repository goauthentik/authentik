import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { SourcesApi, UserLDAPSourceConnection } from "@goauthentik/api";

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
            html`${item.identifier}`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-ldap-users-list": LDAPSourceUserList;
    }
}

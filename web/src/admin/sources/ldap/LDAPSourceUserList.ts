import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#admin/sources/ldap/LDAPSourceUserForm";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { LDAPSource, SourcesApi, UserLDAPSourceConnection } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-source-ldap-users-list")
export class LDAPSourceUserList extends Table<UserLDAPSourceConnection> {
    @property({ attribute: false })
    source?: LDAPSource;

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
            .metadata=${(item: UserLDAPSourceConnection) => {
                return [
                    { key: msg("User"), value: item.userObj.username },
                    { key: msg("ID"), value: item.identifier },
                ];
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    renderToolbar(): TemplateResult {
        return html`<ak-forms-modal cancelText=${msg("Close")} keep-open-after-submit>
                <span slot="submit">${msg("Connect")}</span>
                <span slot="header">${msg("Connect User")}</span>
                <ak-source-ldap-user-form .source=${this.source} slot="form">
                </ak-source-ldap-user-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Connect")}</button>
            </ak-forms-modal>
            ${super.renderToolbar()}`;
    }

    async apiEndpoint(): Promise<PaginatedResponse<UserLDAPSourceConnection>> {
        return new SourcesApi(DEFAULT_CONFIG).sourcesUserConnectionsLdapList({
            ...(await this.defaultEndpointConfig()),
            sourceSlug: this.source?.slug,
        });
    }

    protected override rowLabel(item: UserLDAPSourceConnection): string {
        return item.userObj.name;
    }

    get columns(): TableColumn[] {
        return [
            // ---
            [msg("Name")],
            [msg(str`Object Identifier (${this.source?.objectUniquenessField})`)],
        ];
    }

    row(item: UserLDAPSourceConnection): SlottedTemplateResult[] {
        return [
            html`<a href="#/identity/users/${item.userObj.pk}">
                <div>${item.userObj.username}</div>
                <small>${item.userObj.name}</small>
            </a>`,
            html`<code>${item.identifier}</code>`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-ldap-users-list": LDAPSourceUserList;
    }
}

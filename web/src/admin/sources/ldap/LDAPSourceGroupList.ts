import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#admin/sources/ldap/LDAPSourceGroupForm";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { GroupLDAPSourceConnection, LDAPSource, SourcesApi } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-source-ldap-groups-list")
export class LDAPSourceGroupList extends Table<GroupLDAPSourceConnection> {
    @property({ attribute: false })
    source?: LDAPSource;

    protected override searchEnabled = true;

    checkbox = true;
    clearOnRefresh = true;

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            object-label=${msg("LDAP Group(s)")}
            .objects=${this.selectedElements}
            .delete=${(item: GroupLDAPSourceConnection) => {
                return new SourcesApi(DEFAULT_CONFIG).sourcesGroupConnectionsLdapDestroy({
                    id: item.pk,
                });
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
                <span slot="header">${msg("Connect Group")}</span>
                <ak-source-ldap-group-form .source=${this.source} slot="form">
                </ak-source-ldap-group-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Connect")}</button>
            </ak-forms-modal>
            ${super.renderToolbar()}`;
    }

    async apiEndpoint(): Promise<PaginatedResponse<GroupLDAPSourceConnection>> {
        return new SourcesApi(DEFAULT_CONFIG).sourcesGroupConnectionsLdapList({
            ...(await this.defaultEndpointConfig()),
            sourceSlug: this.source?.slug,
        });
    }

    protected override rowLabel(item: GroupLDAPSourceConnection): string {
        return item.groupObj.name;
    }

    get columns(): TableColumn[] {
        return [
            // ---
            [msg("Name")],
            [msg(str`Object Identifier (${this.source?.objectUniquenessField})`)],
        ];
    }

    row(item: GroupLDAPSourceConnection): SlottedTemplateResult[] {
        return [
            html`<a href="#/identity/groups/${item.groupObj.pk}">
                <div>${item.groupObj.name}</div>
            </a>`,
            html`<code>${item.identifier}</code>`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-ldap-groups-list": LDAPSourceGroupList;
    }
}

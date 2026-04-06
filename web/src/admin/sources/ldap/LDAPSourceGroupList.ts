import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#elements/sync/SyncObjectForm";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import {
    GroupLDAPSourceConnection,
    SourcesApi,
    SourcesGroupConnectionsLdapCreateRequest,
    SyncObjectModelEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-source-ldap-groups-list")
export class LDAPSourceGroupList extends Table<GroupLDAPSourceConnection> {
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
                    .sync=${(data: SourcesGroupConnectionsLdapCreateRequest) => {
                        return new SourcesApi(DEFAULT_CONFIG).sourcesGroupConnectionsLdapCreate(
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

    async apiEndpoint(): Promise<PaginatedResponse<GroupLDAPSourceConnection>> {
        return new SourcesApi(DEFAULT_CONFIG).sourcesGroupConnectionsLdapList({
            ...(await this.defaultEndpointConfig()),
            sourceSlug: this.sourceSlug,
        });
    }

    protected override rowLabel(item: GroupLDAPSourceConnection): string {
        return item.groupObj.name;
    }

    protected columns: TableColumn[] = [
        // ---
        [msg("Name")],
        [msg("ID")],
    ];

    row(item: GroupLDAPSourceConnection): SlottedTemplateResult[] {
        return [
            html`<a href="#/identity/groups/${item.groupObj.pk}">
                <div>${item.groupObj.name}</div>
            </a>`,
            html`${item.pk}`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-ldap-groups-list": LDAPSourceGroupList;
    }
}

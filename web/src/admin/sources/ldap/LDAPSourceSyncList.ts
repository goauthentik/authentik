import "#elements/forms/DeleteBulkForm";
import "#components/tasks/TaskList";
import "#components/tasks/TaskStatus";
import "#elements/forms/ModalForm";
import "#admin/sources/ldap/LDAPSourceUserForm";

import { aki } from "#common/api/client";

import { PaginatedResponse, Table, TableColumn, Timestamp } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import {
    LDAPSource,
    LDAPSourceSync,
    PaginatedLDAPSourceSyncList,
    SourcesApi,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

// prettier-ignore
const noSourceResponse = {
    pagination: {
        next: 0, previous: 0, count: 0, current: 0,
        totalPages: 0, startIndex: 0, endIndex: 0
    },
    results: [],
    autocomplete: {}
} satisfies PaginatedLDAPSourceSyncList;

@customElement("ak-source-ldap-sync-list")
export class LDAPSourceSyncList extends Table<LDAPSourceSync> {
    @property({ attribute: false })
    public source: LDAPSource | null = null;

    public override expandable = true;
    public override clearOnRefresh = true;

    public override order = "-started_at";

    protected async apiEndpoint(): Promise<PaginatedResponse<LDAPSourceSync>> {
        return this.source
            ? aki(SourcesApi).sourcesLdapSyncsList({
                  ...(await this.defaultEndpointConfig()),
                  slug: this.source?.slug,
              })
            : noSourceResponse;
    }

    protected override rowLabel(item: LDAPSourceSync): string {
        return item.pk;
    }

    protected override columns: TableColumn[] = [
        [msg("Status"), "status"],
        [msg("Started"), "started_at"],
        [msg("Finished"), "finished_at"],
        [msg("Users")],
        [msg("Groups")],
        [msg("Memberships")],
        [msg("Group hierarchies")],
    ];

    protected override row(item: LDAPSourceSync): SlottedTemplateResult[] {
        return [
            html`<ak-task-status .status=${item.status}></ak-task-status>`,
            Timestamp(item.startedAt),
            Timestamp(item.finishedAt),
            html`+${item.usersCount ?? 0}/-${item.userDeletionsCount ?? 0}`,
            html`+${item.groupsCount ?? 0}/-${item.groupDeletionsCount ?? 0}`,
            item.membershipCount ?? 0,
            item.groupHierarchyCount ?? 0,
        ];
    }

    protected override renderExpanded(item: LDAPSourceSync): TemplateResult {
        return html`<div class="pf-c-content">
            <ak-task-list .taskIds=${item.tasks}></ak-task-list>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-ldap-sync-list": LDAPSourceSyncList;
    }
}

import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { PaginatedResponse, Table, TableColumn } from "@goauthentik/elements/table/Table";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { SCIMSourceGroup, SourcesApi } from "@goauthentik/api";

@customElement("ak-source-scim-groups-list")
export class SCIMSourceGroupList extends Table<SCIMSourceGroup> {
    @property()
    sourceSlug?: string;

    expandable = true;
    searchEnabled(): boolean {
        return true;
    }

    async apiEndpoint(): Promise<PaginatedResponse<SCIMSourceGroup>> {
        return new SourcesApi(DEFAULT_CONFIG).sourcesScimGroupsList({
            ...(await this.defaultEndpointConfig()),
            sourceSlug: this.sourceSlug,
        });
    }

    columns(): TableColumn[] {
        return [new TableColumn(msg("Name")), new TableColumn(msg("ID"))];
    }

    renderExpanded(item: SCIMSourceGroup): TemplateResult {
        return html`<td role="cell" colspan="4">
            <div class="pf-c-table__expandable-row-content">
                <pre>${JSON.stringify(item.attributes, null, 4)}</pre>
            </div>
        </td>`;
    }

    row(item: SCIMSourceGroup): TemplateResult[] {
        return [
            html`<a href="#/identity/groups/${item.groupObj.pk}">
                <div>${item.groupObj.name}</div>
            </a>`,
            html`${item.id}`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-scim-groups-list": SCIMSourceGroupList;
    }
}

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";

import { SCIMSourceGroup, SourcesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-source-scim-groups-list")
export class SCIMSourceGroupList extends Table<SCIMSourceGroup> {
    @property()
    public sourceSlug?: string;

    public override expandable = true;

    protected override searchEnabled(): boolean {
        return true;
    }

    protected async apiEndpoint(): Promise<PaginatedResponse<SCIMSourceGroup>> {
        return new SourcesApi(DEFAULT_CONFIG).sourcesScimGroupsList({
            ...(await this.defaultEndpointConfig()),
            sourceSlug: this.sourceSlug,
        });
    }

    protected columns(): TableColumn[] {
        return [new TableColumn(msg("Name")), new TableColumn(msg("ID"))];
    }

    protected override renderExpanded(item: SCIMSourceGroup): TemplateResult {
        return html`<td role="cell" colspan="4">
            <div class="pf-c-table__expandable-row-content">
                <pre>${JSON.stringify(item.attributes, null, 4)}</pre>
            </div>
        </td>`;
    }

    protected row(item: SCIMSourceGroup): TemplateResult[] {
        return [
            html`<a href="#/identity/groups/${item.groupObj.pk}">
                <div>${item.groupObj.name}</div>
            </a>`,
            html`${item.externalId}`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-scim-groups-list": SCIMSourceGroupList;
    }
}

import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#elements/sync/SyncObjectForm";
import "#admin/common/ak-flow-search/ak-flow-search-no-default";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { Outpost, Provider } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-outposts-provider-list")
export class OutpostsProviderList extends Table<Provider> {
    @property({ attribute: false })
    public outpost: Outpost | null = null;

    protected override searchEnabled = false;

    checkbox = true;
    clearOnRefresh = true;

    async apiEndpoint(): Promise<PaginatedResponse<Provider>> {
        const items = this.outpost?.providersObj || [];
        return {
            pagination: {
                count: items.length,
                current: 1,
                totalPages: 1,
                startIndex: 1,
                endIndex: items.length,
                next: 0,
                previous: 0,
            },
            results: items,
        };
    }

    protected columns: TableColumn[] = [
        // ---
        [msg("Name")],
        [msg("ID")],
    ];

    row(item: Provider): SlottedTemplateResult[] {
        return [
            html`<a href="#/core/providers/${item.pk}">
                <div>${item.name}</div>
            </a>`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-outposts-provider-list": OutpostsProviderList;
    }
}

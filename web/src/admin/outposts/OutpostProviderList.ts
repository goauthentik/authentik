import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#elements/sync/SyncObjectForm";
import "#admin/common/ak-flow-search/ak-flow-search-no-default";

import { StaticTable } from "#elements/table/StaticTable";
import { TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { Provider } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-outposts-provider-list")
export class OutpostsProviderList extends StaticTable<Provider> {
    protected emptyStateMessage: string = msg("No providers configured.");
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

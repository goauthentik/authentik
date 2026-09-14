import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#components/sync/SyncObjectForm";
import "#admin/common/ak-flow-search/ak-flow-search-no-default";

import { toAdminInterface } from "#elements/router/core/interfaces";
import { StaticTable } from "#elements/table/StaticTable";
import { TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { Provider } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-outposts-provider-list")
export class OutpostsProviderList extends StaticTable<Provider> {
    protected emptyStateMessage: string = msg("No providers configured.");
    protected columns: TableColumn[] = [
        // ---
        [msg("Name")],
        [msg("Application")],
    ];

    row(item: Provider): SlottedTemplateResult[] {
        return [
            html`<a href=${toAdminInterface(`core/providers/${item.pk}`)}>
                <div>${item.name}</div>
            </a>`,
            item.assignedApplicationName
                ? html`<a
                      href=${toAdminInterface(`core/applications/${item.assignedApplicationSlug}`)}
                  >
                      <div>${item.assignedApplicationName}</div>
                  </a>`
                : nothing,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-outposts-provider-list": OutpostsProviderList;
    }
}

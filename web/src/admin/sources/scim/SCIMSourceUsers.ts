import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { SCIMSourceUser, SourcesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-source-scim-users-list")
export class SCIMSourceUserList extends Table<SCIMSourceUser> {
    @property()
    sourceSlug?: string;

    expandable = true;
    protected override searchEnabled = true;

    async apiEndpoint(): Promise<PaginatedResponse<SCIMSourceUser>> {
        return new SourcesApi(DEFAULT_CONFIG).sourcesScimUsersList({
            ...(await this.defaultEndpointConfig()),
            sourceSlug: this.sourceSlug,
        });
    }

    protected override rowLabel(item: SCIMSourceUser): string {
        return item.userObj.name || item.userObj.username;
    }

    protected columns: TableColumn[] = [
        // ---
        [msg("Username")],
        [msg("ID")],
    ];

    renderExpanded(item: SCIMSourceUser): TemplateResult {
        return html`<pre>${JSON.stringify(item.attributes, null, 4)}</pre>`;
    }

    row(item: SCIMSourceUser): SlottedTemplateResult[] {
        return [
            html`<a href="#/identity/users/${item.userObj.pk}">
                <div>${item.userObj.username}</div>
                <small>${item.userObj.name}</small>
            </a>`,
            html`${item.externalId}`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-scim-users-list": SCIMSourceUserList;
    }
}

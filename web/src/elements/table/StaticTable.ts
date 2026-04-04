import { createPaginatedResponse } from "#common/api/responses";

import { PaginatedResponse, Table } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { PropertyValues } from "lit";
import { html, nothing } from "lit-html";
import { property } from "lit/decorators.js";

export abstract class StaticTable<T extends object> extends Table<T> {
    protected override searchEnabled = false;

    @property({ attribute: false })
    items?: T[] = [];

    protected override async apiEndpoint(): Promise<PaginatedResponse<T, object>> {
        return createPaginatedResponse(this.items ?? []);
    }

    protected override renderToolbar(): SlottedTemplateResult {
        return html`${this.renderObjectCreate()}`;
    }

    protected override renderTablePagination(): SlottedTemplateResult {
        return nothing;
    }

    protected override willUpdate(changedProperties: PropertyValues<this>): void {
        if (changedProperties.has("items")) {
            this.fetch();
        }
        super.willUpdate(changedProperties);
    }
}

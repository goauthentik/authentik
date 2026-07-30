import { createPaginatedResponse } from "#common/api/responses";

import { PaginatedResponse, Table } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { PropertyValues } from "lit";
import { property } from "lit/decorators.js";

export abstract class StaticTable<T extends object> extends Table<T> {
    protected override searchEnabled = false;

    @property({ attribute: false })
    public items: T[] | null = [];

    protected override async apiEndpoint(): Promise<PaginatedResponse<T, object>> {
        return createPaginatedResponse(this.items ?? []);
    }

    protected override renderToolbar(): SlottedTemplateResult {
        return this.renderObjectCreate();
    }

    protected override renderTablePagination(): SlottedTemplateResult {
        return null;
    }

    protected override willUpdate(changedProperties: PropertyValues<this>): void {
        if (changedProperties.has("items")) {
            this.fetch();
        }

        super.willUpdate(changedProperties);
    }
}

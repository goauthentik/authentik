import { TableLike } from "#elements/table/shared";

import { html, TemplateResult } from "lit";
import { classMap } from "lit/directives/class-map.js";

type ARIASort = "ascending" | "descending" | "none" | "other";

export class TableColumn {
    title: string;
    orderBy?: string;

    onClick?: () => void;

    constructor(title: string, orderBy?: string) {
        this.title = title;
        this.orderBy = orderBy;
    }

    //#region Sorting

    #sortButtonListener(table: TableLike): void {
        if (!this.orderBy) {
            return;
        }

        table.order = table.order === this.orderBy ? `-${this.orderBy}` : this.orderBy;
        table.fetch();
    }

    private getSortIndicator(table: TableLike): string {
        switch (this.getARIASort(table)) {
            case "ascending":
                return "fa-long-arrow-alt-up";
            case "descending":
                return "fa-long-arrow-alt-down";
            default:
                return "fa-arrows-alt-v";
        }
    }

    public getARIASort(table: TableLike): ARIASort {
        switch (table.order) {
            case this.orderBy:
                return "ascending";
            case `-${this.orderBy}`:
                return "descending";
            default:
                return "none";
        }
    }

    protected renderSortable(table: TableLike): TemplateResult {
        return html` <button
            class="pf-c-table__button"
            @click=${() => this.#sortButtonListener(table)}
        >
            <div class="pf-c-table__button-content">
                <span class="pf-c-table__text">${this.title}</span>
                <span class="pf-c-table__sort-indicator">
                    <i aria-hidden="true" class="fas ${this.getSortIndicator(table)}"></i>
                </span>
            </div>
        </button>`;
    }

    public render(table: TableLike): TemplateResult {
        const classes = {
            "pf-c-table__sort": !!this.orderBy,
            "pf-m-selected": table.order === this.orderBy || table.order === `-${this.orderBy}`,
        };

        return html`<th
            role="columnheader"
            scope="col"
            aria-sort=${this.getARIASort(table)}
            class="${classMap(classes)}"
        >
            ${this.orderBy ? this.renderSortable(table) : html`${this.title}`}
        </th>`;
    }
}

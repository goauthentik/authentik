import { TableLike } from "#elements/table/shared";

import { msg, str } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { classMap } from "lit/directives/class-map.js";
import { ifDefined } from "lit/directives/if-defined.js";

type SortDirection = "ascending" | "descending" | "none" | "other";

function formatSortIndicator(direction: SortDirection): string {
    switch (direction) {
        case "ascending":
            return "fa-long-arrow-alt-up";
        case "descending":
            return "fa-long-arrow-alt-down";
        default:
            return "fa-arrows-alt-v";
    }
}

function formatSortDirection(table: TableLike, orderBy?: string): SortDirection {
    switch (table.order) {
        case orderBy:
            return "ascending";
        case `-${orderBy}`:
            return "descending";
        default:
            return "none";
    }
}

export type TableColumn = [label: string, orderBy?: string, ariaLabel?: string];

const formatColumnID = (columnIndex: number): string => `table-header-${columnIndex}`;

export interface TableColumnProps {
    label: string;
    ariaLabel?: string;
    orderBy?: string;
    table: TableLike;
    columnIndex: number;
}

export function renderTableColumn({
    label,
    ariaLabel,
    orderBy,
    table,
    columnIndex,
}: TableColumnProps): TemplateResult {
    const classes = {
        "pf-c-table__sort": !!orderBy,
        "pf-m-selected": table.order === orderBy || table.order === `-${orderBy}`,
    };

    const sortButtonListener = () => {
        if (!orderBy) return;

        table.order = table.order === orderBy ? `-${orderBy}` : orderBy;
        table.fetch();
    };

    const direction = formatSortDirection(table, orderBy);

    const content = orderBy
        ? html` <button
              aria-label=${msg(str`Sort by ${label}`)}
              class="pf-c-table__button"
              @click=${sortButtonListener}
          >
              <div class="pf-c-table__button-content">
                  <span class="pf-c-table__text">${label}</span>
                  <span class="pf-c-table__sort-indicator">
                      <i aria-hidden="true" class="fas ${formatSortIndicator(direction)}"></i>
                  </span>
              </div>
          </button>`
        : html`${label}`;

    return html`<th
        id=${formatColumnID(columnIndex)}
        aria-label=${ifDefined(ariaLabel ?? label)}
        data-column-id=${ifDefined(orderBy)}
        role="columnheader"
        scope="col"
        aria-sort=${direction}
        class="${classMap(classes)}"
    >
        ${content}
    </th>`;
}

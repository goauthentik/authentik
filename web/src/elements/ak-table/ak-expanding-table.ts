import { bound } from "@goauthentik/elements/decorators/bound";

import { html } from "lit";
import { customElement } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { map } from "lit/directives/map.js";

import { ExpansionRenderer } from "./ExpansionRenderer.js";
import { SimpleTable } from "./ak-simple-table";
import type { TableRow } from "./types";

const ExpansionTableBase = ExpansionRenderer(SimpleTable);

/**
 * @element ak-expandable-table
 * class Table
 *
 * Extends the SimpleTable with...
 *
 * ## Properties
 *
 * - @prop content (see types): The content to show. The simplest content is just `string[][]`, but
 *   see the types.
 *
 * - @prop columns (see types): The column headers for the table.  Can be just a `string[]`, but see
 *   the types.
 *
 * - @attr (string, optional): The current column to order the content by.  By convention, prefix
 *   with a `-` to indicate a reverse sort order.  (See "Does not handle sorting" above).
 *
 * ## Events
 *
 * - @fires tablesort (Custom): A table header has been clicked, requesting a sort event. See "Does
 *   not handle sorting" above.
 *
 * ## CSS Customizations
 *
 * - @part table: the `<table>` element
 * - @part column-header: the `<thead>` element for the column headers themselves
 * - @part column-row: The `<tr>` element for the column headers
 * - @part column-item: The `<th>` element for each column header
 * - @part column-text: The text `<span>` of the column header
 * - @part column-sort: The sort indicator `<span>` of a column header, if activated
 * - @part group-header: The `<thead>` element for a group header
 * - @part group-row: The `<tr>` element for a group header
 * - @part group-head: The `<th>` element for a group header
 * - @part row: The `<tr>` element for a standard row
 * - @part cell cell-{index}: The `<td>` element for a single datum. Can be accessed via the index,
 *   which is zero-indexed
 * - @part expand-cell: The `<td>` of the button that controls expansion
 * - @part expand-icon: The `<div>` that contains the expansion icon
 * - @part expansion-row: The `<tr>` that contains the expanded content.
 * - @part expansion-cell: The `<td>` that contains the expanded content.
 *
 * NOTE: The expand-cell is *not* indexed. The `::part(cell-{idx})` remains indexed by zero; you
 * cannot access the expand-cell via `cell-0`; that would be the first data column. This is due to a
 * limitation on the `part::` semantics.
 *
 */

@customElement("ak-expandable-table")
export class ExpandableTable extends ExpansionTableBase {
    // Without the `bound`, Lit's `map()` will pick up the parent class's `renderRow()`.
    @bound
    public override renderRow(row: TableRow, rowidx: number) {
        const expanded = this.expandedRows.includes(rowidx);
        const expandedClass = { "pf-m-expanded": expanded };
        return html`
            <tr part="row" class=${classMap(expandedClass)}>
                ${this.renderExpansionControl(rowidx, expanded)}
                ${map(
                    row.content,
                    (col, idx) => html`<td part="cell cell-${idx}" role="cell">${col}</td>`,
                )}
            </tr>
            ${this.renderExpansion(row, expanded)}
        `;
    }

    public override renderColumnHeaders() {
        return html`<tr part="column-row" role="row">
            <td role="cell"></td>
            ${map(this.icolumns, (col) => col.render(this.order))}
        </tr>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-expandable-table": ExpandableTable;
    }
}

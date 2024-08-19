import { bound } from "@goauthentik/elements/decorators/bound";

import { html } from "lit";
import { customElement } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { map } from "lit/directives/map.js";

import { ExpansionRenderer } from "./ExpansionRenderer.js";
import { SelectTable } from "./ak-select-table";
import type { TableRow } from "./types";

const FullTableBase = ExpansionRenderer(SelectTable);

/**
 * @element ak-expandable-table
 * class Table
 *
 * Extends the SelectTable with an expansion row that can be shown below a content row.
 *
 * Because both this implementation and `ak-expanding-table` use the exact same rendering
 * infrastructure, that has been broken out into a mixin named
 * [`ExpansionRenderer`](./ExpansionRenderer.ts).
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
 * - @attr (string, optional): The current column to order the content by.  By convention, prefix
 *   with a `-` to indicate a reverse sort order.  (See "Does not handle sorting" above).
 *
 * - @attr multiple (boolean): If true, this table is "multi-select" and a 'select all' checkbox will
 *   be available.
 *
 * - @attr value (string): If set, will set the value of the component. For multi-select, will split
 *   on the `valueSep` (see next entry).  Get is the reverse: either the value of the component,
 *   or for multi-select, the value of the component `.join()`ed with the `valueSep`
 *
 * - @attr valueSep (string): For multi-select only, the (ideally one) characters which will separate
 *   values.
 *
 * - @prop selected (string[]): The values selected. Always an array, even for mult-select. When not
 *   multi-select, will have zero or one items only.
 *
 * ## Events
 *
 * - @fires tablesort (Custom): A table header has been clicked, requesting a sort event. See "Does
 *   not handle sorting" above.
 *
 * - @fires change: Notifies clients that the user has changed the collective value of the control.
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
 * - @part select-all-header: The `<th>` element for the select-all checkbox, when _multiple_
 * - @part select-all-input: The `<input>` element for the select-all checkbox, when _multiple_
 * - @part select-cell: The `<td>` element for a select checkbox
 * - @part select-input: The `<input> element for a select checkbox
 * - @part expand-cell: The `<td>` of the button that controls expansion
 * - @part expand-icon: The `<div>` that contains the expansion icon
 * - @part expansion-row: The `<tr>` that contains the expanded content.
 * - @part expansion-cell: The `<td>` that contains the expanded content.
 *
 * NOTE: Neither the expand-cell or select-cell is indexed. The `::part(cell-{idx})` remains indexed
 * by zero; you cannot access the expand-cell or select-cell via `cell-0`; that would be the first
 * data column. This is due to a limitation on the `part::` semantics.
 *
 */

@customElement("ak-table-view")
export class TableView extends FullTableBase {
    protected override ouiaTypeDeclaration() {
        this.setAttribute("data-ouia-component-type", "ak-full-table");
    }

    // Without the `bound`, Lit's `map()` will pick up the parent class's `renderRow()`. This
    // override adds the expansion control and expansion row rendering to this method, while
    // preserving room for the select control.
    @bound
    public override renderRow(row: TableRow, rowidx: number) {
        const expanded = this.expandedRows.includes(rowidx);
        const expandedClass = { "pf-m-expanded": expanded };
        return html`
            <tr part="row" class=${classMap(expandedClass)}>
                ${this.renderCheckbox(row.key)}
                <!-- prettier-ignore -->
                ${this.renderExpansionControl(rowidx, expanded)}
                ${map(
                    row.content,
                    (col, idx) => html`<td part="cell cell-${idx}" role="cell">${col}</td>`,
                )}
            </tr>
            ${this.renderExpansion(row, expanded)}
        `;
    }

    // This override adds room for the expansion control, while also providing room
    // for the `select` control.
    public override renderColumnHeaders() {
        return html`<tr part="column-row" role="row">
            <td role="cell"></td>
            ${this.multiple ? this.renderAllOnThisPageCheckbox() : html`<th></th>`}
            ${map(this.icolumns, (col) => col.render(this.order))}
        </tr>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-table-view": TableView;
    }
}

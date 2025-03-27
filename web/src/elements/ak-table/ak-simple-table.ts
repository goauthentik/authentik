import { AKElement } from "@goauthentik/elements/Base.js";
import { bound } from "@goauthentik/elements/decorators/bound";
import { randomId } from "@goauthentik/elements/utils/randomId.js";

import { TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { map } from "lit/directives/map.js";
import { repeat } from "lit/directives/repeat.js";

import PFTable from "@patternfly/patternfly/components/Table/table.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { TableColumn } from "./TableColumn.js";
import type { Column, TableFlat, TableGroup, TableGrouped, TableRow } from "./types";
import { convertContent } from "./utils";

export type RawContent = string | number | TemplateResult;
export type ContentType = RawContent[][] | TableRow[] | TableGrouped;

export interface ISimpleTable {
    columns: Column[];
    content: TableGrouped | TableFlat;
    order?: string;
}

/**
 * @element ak-simple-table
 * class Table
 *
 * Our simplest table. It takes a column definition and an array (rows) of array (one row) of
 * TemplateResults, and it renders a table. If the column definition includes keys, the column will
 * be rendered with a sort indicator.
 *
 * ## Does not handle sorting.
 *
 * ... that's _all_ this does. It is the responsibility of clients using this table to:
 *
 * - marshall their content into TemplateResults
 * - catch the 'tablesort' event and send the table a new collection of rows sorted according to
 *   the client scheme.
 *
 * ## Properties
 *
 * - @prop content (see types): The content to show. The simplest content is just `string[][]`, but
 *   see the types.
 *
 * - @prop columns (see types): The column headers for the table.  Can be just a `string[]`, but see
 *   the types.
 *
 * - @attr order (string, optional): The current column to order the content by.  By convention, prefix
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
 *
 */

@customElement("ak-simple-table")
export class SimpleTable extends AKElement implements ISimpleTable {
    static get styles() {
        return [
            PFBase,
            PFTable,
            css`
                .pf-c-table thead .pf-c-table__check {
                    min-width: 3rem;
                }
                .pf-c-table tbody .pf-c-table__check input {
                    margin-top: calc(var(--pf-c-table__check--input--MarginTop) + 1px);
                }
                .pf-c-toolbar__content {
                    row-gap: var(--pf-global--spacer--sm);
                }
                .pf-c-toolbar__item .pf-c-input-group {
                    padding: 0 var(--pf-global--spacer--sm);
                }
            `,
        ];
    }

    @property({ type: String, attribute: true, reflect: true })
    order?: string;

    @property({ type: Array, attribute: false })
    columns: Column[] = [];

    @property({ type: Object, attribute: false })
    set content(content: ContentType) {
        this._content = convertContent(content);
    }

    get content(): TableGrouped | TableFlat {
        return this._content;
    }

    private _content: TableGrouped | TableFlat = {
        kind: "flat",
        content: [],
    };

    protected get icolumns(): TableColumn[] {
        const hosted = (column: TableColumn) => {
            column.host = this;
            return column;
        };

        return this.columns.map((column) =>
            typeof column === "string"
                ? hosted(new TableColumn(column))
                : Array.isArray(column)
                  ? hosted(new TableColumn(...column))
                  : hosted(column),
        );
    }

    protected ouiaTypeDeclaration() {
        this.setAttribute("data-ouia-component-type", "ak-simple-table");
    }

    public override connectedCallback(): void {
        super.connectedCallback();
        this.ouiaTypeDeclaration();
        this.setAttribute("data-ouia-component-id", this.getAttribute("id") || randomId());
    }

    public override performUpdate() {
        this.removeAttribute("data-ouia-component-safe");
        super.performUpdate();
    }

    public renderRow(row: TableRow, _rownum: number) {
        return html` <tr part="row">
            ${map(
                row.content,
                (col, idx) => html`<td part="cell cell-${idx}" role="cell">${col}</td>`,
            )}
        </tr>`;
    }

    public renderRows(rows: TableRow[]) {
        return html`<tbody part="body">
            ${repeat(rows, (row) => row.key, this.renderRow)}
        </tbody>`;
    }

    @bound
    public renderRowGroup({ group, content }: TableGroup) {
        return html`<thead part="group-header">
                <tr part="group-row">
                    <td role="columnheader" scope="row" colspan="200" part="group-head">
                        ${group}
                    </td>
                </tr>
            </thead>
            ${this.renderRows(content)}`;
    }

    @bound
    public renderRowGroups(rowGroups: TableGroup[]) {
        return html`${map(rowGroups, this.renderRowGroup)}`;
    }

    public renderBody() {
        // prettier-ignore
        return this.content.kind === 'flat'
            ? this.renderRows(this.content.content)
            : this.renderRowGroups(this.content.content);
    }

    public renderColumnHeaders() {
        return html`<tr part="column-row" role="row">
            ${map(this.icolumns, (col) => col.render(this.order))}
        </tr>`;
    }

    public renderTable() {
        return html`
            <table part="table" class="pf-c-table pf-m-compact pf-m-grid-md pf-m-expandable">
                <thead part="column-header">
                    ${this.renderColumnHeaders()}
                </thead>
                ${this.renderBody()}
            </table>
        `;
    }

    public render() {
        return this.renderTable();
    }

    public override updated() {
        this.setAttribute("data-ouia-component-safe", "true");
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-simple-table": SimpleTable;
    }
}

import { AKElement } from "@goauthentik/elements/Base.js";
import "@goauthentik/elements/table/standalone/table.js";

import { html } from "lit";
import { TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { map } from "lit/directives/map.js";

import PFTable from "@patternfly/patternfly/components/Table/table.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { TableColumn } from "./TableColumn.js";
import type { Column, TableFlat, TableGroup, TableGrouped, TableRow } from "./types";
import { groupContent } from "./utils";

/**
 * @element ak-simple-table
 * class Table
 *
 * Our simplest table. It takes a column definition and an array (rows) of array (one row) of
 * TemplateResults, and it renders a table. If the column definition includes keys, the column will
 * be rendered with a sort indicator.
 *
 * ... and that's _all_ this does. It is the responsibility of clients using this table to:
 * - marshall their content into TemplateResults and
 * - catch the 'tablesort' event and send the table a new collection of rows sorted according to the
 *   client scheme.
 */

@customElement("ak-simple-table")
export class SimpleTable extends AKElement {
    static get styles() {
        return [PFBase, PFTable];
    }

    @property({ type: String, reflect: true })
    order?: string;

    @property({ type: Array, attribute: false })
    columns: Column[] = [];

    @property({ type: Array, attribute: false })
    set content(content: TemplateResult[][] | TableRow[] | TableGrouped) {
        this._content = groupContent(content);
    }

    get content(): TableGrouped | TableFlat {
        return this._content;
    }

    _content: TableGrouped | TableFlat = {
        kind: "table-flat",
        content: [],
    };

    private get icolumns(): TableColumn[] {
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

    public renderRow(row: TableRow) {
        return html` <tr>
            ${map(row.content, (col) => html`<td role="cell">${col}</td>`)}
        </tr>`;
    }

    public renderRows(rows: TableRow[]) {
        return html`<tbody>
            ${map(rows, this.renderRow)}
        </tbody>`;
    }

    public renderRowGroup({ group, content }: TableGroup) {
        return html`<thead>
                <tr>
                    <th role="columnheader" scope="row" colspan="200">${group}</th>
                </tr>
            </thead>
            ${this.renderRows(content)}`;
    }

    public renderRowGroups(rowGroups: TableGroup[]) {
        return html`${map(rowGroups, this.renderRowGroup)}`;
    }

    public renderBody() {
        // prettier-ignore
        return this.content.kind === 'table-flat' 
            ? this.renderRows(this.content.content)
            : this.renderRowGroups(this.content.content);
    }

    public renderColumnHeaders() {
        return html`<tr role="row">
            ${map(this.icolumns, (col) => col.render(this.order))}
        </tr>`;
    }

    public renderTable() {
        return html`
            <table class="pf-c-table pf-m-compact pf-m-grid-md pf-m-expandable">
                <thead>
                    ${this.renderColumnHeaders()}
                </thead>
                ${this.renderBody()}
            </table>
        `;
    }

    public render() {
        return this.renderTable();
    }
}

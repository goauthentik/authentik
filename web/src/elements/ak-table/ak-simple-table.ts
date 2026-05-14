import "#elements/EmptyState";

import { TableColumn } from "./TableColumn.js";
import type { Column, TableFlat, TableGroup, TableGrouped, TableRow } from "./types.js";
import { convertContent } from "./utils.js";

import { AKElement } from "#elements/Base";
import {
    EntityDescriptorElement,
    isTransclusionParentElement,
    TransclusionChildElement,
    TransclusionChildSymbol,
} from "#elements/dialogs/shared";
import { WithLocale } from "#elements/mixins/locale";
import { SlottedTemplateResult } from "#elements/types";
import { randomId } from "#elements/utils/randomId";

import { msg, str } from "@lit/localize";
import { css, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { map } from "lit/directives/map.js";
import { repeat } from "lit/directives/repeat.js";

import PFTable from "@patternfly/patternfly/components/Table/table.css";

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
export class SimpleTable
    extends WithLocale(AKElement)
    implements ISimpleTable, TransclusionChildElement
{
    declare ["constructor"]: Required<EntityDescriptorElement>;

    public static verboseName: string = msg("Object");
    public static verboseNamePlural: string = msg("Objects");

    public static styles = [
        PFTable,
        css`
            .pf-c-toolbar__content {
                row-gap: var(--pf-global--spacer--sm);
            }
            .pf-c-toolbar__item .pf-c-input-group {
                padding: 0 var(--pf-global--spacer--sm);
            }

            tr:last-child {
                --pf-c-table--BorderColor: transparent;
            }
        `,
    ];

    public [TransclusionChildSymbol] = true;

    #verboseName: string | null = null;

    /**
     * Optional singular label for the type of entity this form creates/edits.
     *
     * Overrides the static `verboseName` property for this instance.
     */
    @property({ type: String, attribute: "entity-singular" })
    public set verboseName(value: string | null) {
        this.#verboseName = value;

        if (isTransclusionParentElement(this.parentElement)) {
            this.parentElement.slottedElementUpdatedAt = new Date();
        }
    }

    public get verboseName(): string | null {
        return this.#verboseName || this.constructor.verboseName || null;
    }

    #verboseNamePlural: string | null = null;

    /**
     * Optional plural label for the type of entity this form creates/edits.
     *
     * Overrides the static `verboseNamePlural` property for this instance.
     */
    @property({ type: String, attribute: "entity-plural" })
    public set verboseNamePlural(value: string | null) {
        this.#verboseNamePlural = value;

        if (isTransclusionParentElement(this.parentElement)) {
            this.parentElement.slottedElementUpdatedAt = new Date();
        }
    }

    public get verboseNamePlural(): string | null {
        return this.#verboseNamePlural || this.constructor.verboseNamePlural || null;
    }

    @property({ type: String, attribute: true, reflect: true })
    public order?: string;

    @property({ type: Array, attribute: false })
    public columns: Column[] = [];

    @property({ type: Object, attribute: false })
    public set content(content: ContentType) {
        this.#content = convertContent(content);
    }

    public get content(): TableGrouped | TableFlat {
        return this.#content;
    }

    #content: TableGrouped | TableFlat = {
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

    protected renderEmpty(): SlottedTemplateResult {
        const columnCount = this.columns.length || 1;

        const verboseNamePlural = this.constructor.verboseNamePlural || msg("Objects");
        const message = msg(
            str`No ${verboseNamePlural.toLocaleLowerCase(this.activeLanguageTag)} found.`,
            {
                id: "table.empty",
                desc: "The message to show when a table has no content. The placeholder {0} is replaced with the pluralized name of the type of entity being shown in the table.",
            },
        );

        return html`<tr role="presentation">
            <td role="presentation" colspan=${columnCount + 1}>
                <div class="pf-l-bullseye">
                    <slot name="empty-table">
                        <ak-empty-state><span>${message}</span></ak-empty-state>
                    </slot>
                </div>
            </td>
        </tr>`;
    }

    protected renderRow(row: TableRow, _rownum: number): SlottedTemplateResult {
        return html`<tr part="row">
            ${map(row.content, (col, idx) => html`<td part="cell cell-${idx}">${col}</td>`)}
        </tr>`;
    }

    protected renderRows(rows: TableRow[]): SlottedTemplateResult {
        return html`<tbody part="body">
            ${rows.length ? repeat(rows, (row) => row.key, this.renderRow) : this.renderEmpty()}
        </tbody>`;
    }

    protected renderRowGroup = ({ group, content }: TableGroup): SlottedTemplateResult => {
        return html`<thead part="group-header">
                <tr part="group-row">
                    <td colspan="200" part="group-head">${group}</td>
                </tr>
            </thead>
            ${this.renderRows(content)}`;
    };

    protected renderRowGroups = (rowGroups: TableGroup[]): SlottedTemplateResult => {
        return map(rowGroups, this.renderRowGroup);
    };

    protected renderBody(): SlottedTemplateResult {
        return this.content.kind === "flat"
            ? this.renderRows(this.content.content)
            : this.renderRowGroups(this.content.content);
    }

    protected renderColumnHeaders(): SlottedTemplateResult {
        return html`<tr part="column-row" role="row">
            ${map(this.icolumns, (col) => col.render(this.order))}
        </tr>`;
    }

    protected renderTable(): SlottedTemplateResult {
        return html`<table
            part="table"
            class="pf-c-table pf-m-compact pf-m-grid-md pf-m-expandable"
        >
            <thead part="column-header">
                ${this.renderColumnHeaders()}
            </thead>
            ${this.renderBody()}
        </table> `;
    }

    protected render(): SlottedTemplateResult {
        return this.renderTable();
    }

    public override updated(): void {
        this.setAttribute("data-ouia-component-safe", "true");
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-simple-table": SimpleTable;
    }
}

import { gettext } from "django";
import { CSSResult, html, LitElement, property, TemplateResult } from "lit-element";
import { PBResponse } from "../../api/Client";
import { COMMON_STYLES } from "../../common/styles";

import "./TablePagination";
import "../EmptyState";


export class TableColumn {

    title: string;
    orderBy?: string;

    onClick?: () => void;

    constructor(title: string, orderBy?: string) {
        this.title = title;
        this.orderBy = orderBy;
    }

    headerClickHandler(table: Table<unknown>): void {
        if (!this.orderBy) {
            return;
        }
        if (table.order === this.orderBy) {
            table.order = `-${this.orderBy}`;
        } else {
            table.order = this.orderBy;
        }
        table.fetch();
    }

    private getSortIndicator(table: Table<unknown>): string {
        switch (table.order) {
        case this.orderBy:
            return "fa-long-arrow-alt-down";
        case `-${this.orderBy}`:
            return "fa-long-arrow-alt-up";
        default:
            return "fa-arrows-alt-v";
        }
    }

    renderSortable(table: Table<unknown>): TemplateResult {
        return html`
            <button class="pf-c-table__button" @click=${() => this.headerClickHandler(table)}>
                <div class="pf-c-table__button-content">
                    <span class="pf-c-table__text">${gettext(this.title)}</span>
                    <span class="pf-c-table__sort-indicator">
                        <i class="fas ${this.getSortIndicator(table)}"></i>
                    </span>
                </div>
            </button>`;
    }

    render(table: Table<unknown>): TemplateResult {
        return html`<th
            role="columnheader"
            scope="col"
            class="
                ${this.orderBy ? "pf-c-table__sort " : " "}
                ${(table.order === this.orderBy || table.order === `-${this.orderBy}`) ? "pf-m-selected " : ""}
            ">
            ${this.orderBy ? this.renderSortable(table) : html`${gettext(this.title)}`}
        </th>`;
    }

}

export abstract class Table<T> extends LitElement {
    abstract apiEndpoint(page: number): Promise<PBResponse<T>>;
    abstract columns(): TableColumn[];
    abstract row(item: T): TemplateResult[];

    private isLoading = false;

    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    renderExpanded(item: T): TemplateResult {
        if (this.expandable) {
            throw new Error("Expandable is enabled but renderExpanded is not overridden!");
        }
        return html``;
    }

    @property({attribute: false})
    data?: PBResponse<T>;

    @property({type: Number})
    page = 1;

    @property({type: String})
    order?: string;

    @property({type: String})
    search?: string;

    @property({type: Boolean})
    expandable = false;

    @property({attribute: false})
    expandedRows: boolean[] = [];

    static get styles(): CSSResult[] {
        return COMMON_STYLES;
    }

    constructor() {
        super();
        this.addEventListener("ak-refresh", () => {
            this.fetch();
        });
    }

    public fetch(): void {
        if (this.isLoading) {
            return;
        }
        this.isLoading = true;
        this.data = undefined;
        this.apiEndpoint(this.page).then((r) => {
            this.data = r;
            this.page = r.pagination.current;
            this.expandedRows = [];
            this.isLoading = false;
        }).catch(() => {
            this.isLoading = false;
        });
    }

    private renderLoading(): TemplateResult {
        return html`<tr role="row">
            <td role="cell" colspan="25">
                <div class="pf-l-bullseye">
                    <div class="pf-c-empty-state pf-m-sm">
                        <div class="pf-c-empty-state__content">
                            <div class="pf-c-empty-state__icon">
                                <span class="pf-c-spinner" role="progressbar">
                                    <span class="pf-c-spinner__clipper"></span>
                                    <span class="pf-c-spinner__lead-ball"></span>
                                    <span class="pf-c-spinner__tail-ball"></span>
                                </span>
                            </div>
                            <h2 class="pf-c-title pf-m-lg">${gettext("Loading")}</h2>
                        </div>
                    </div>
                </div>
            </td>
        </tr>`;
    }

    renderEmpty(inner?: TemplateResult): TemplateResult {
        return html`<tbody role="rowgroup">
            <tr role="row">
                <td role="cell" colspan="8">
                    <div class="pf-l-bullseye">
                        ${inner ? inner : html`<ak-empty-state header="${gettext("No elements found.")}"></ak-empty-state>`}
                    </div>
                </td>
            </tr>
        </tbody>`;
    }

    private renderRows(): TemplateResult[] | undefined {
        if (!this.data) {
            return;
        }
        if (this.data.pagination.count === 0) {
            return [this.renderEmpty()];
        }
        return this.data.results.map((item: T, idx: number) => {
            if ((this.expandedRows.length - 1) < idx) {
                this.expandedRows[idx] = false;
            }
            return html`<tbody role="rowgroup" class="${this.expandedRows[idx] ? "pf-m-expanded" : ""}">
                <tr role="row">
                    ${this.expandable ? html`<td class="pf-c-table__toggle" role="cell">
                    <button class="pf-c-button pf-m-plain ${this.expandedRows[idx] ? "pf-m-expanded" : ""}" @click=${() => {
                        this.expandedRows[idx] = !this.expandedRows[idx];
                        this.requestUpdate();
                    }}>
                        <div class="pf-c-table__toggle-icon"> <i class="fas fa-angle-down" aria-hidden="true"></i> </div>
                    </button>
                    </td>` : html``}
                    ${this.row(item).map((col) => {
                        return html`<td role="cell">${col}</td>`;
                    })}
                </tr>
                <tr class="pf-c-table__expandable-row ${this.expandedRows[idx] ? "pf-m-expanded" : ""}" role="row">
                    <td></td>
                    ${this.expandedRows[idx] ? this.renderExpanded(item) : html``}
                </tr>
            </tbody>`;
        });
    }

    renderToolbar(): TemplateResult {
        return html`&nbsp;<button
            @click=${() => { this.fetch(); }}
            class="pf-c-button pf-m-primary">
            ${gettext("Refresh")}
        </button>&nbsp;`;
    }

    renderToolbarAfter(): TemplateResult {
        return html``;
    }

    renderSearch(): TemplateResult {
        return html``;
    }

    firstUpdated(): void {
        this.fetch();
    }

    renderTable(): TemplateResult {
        return html`<div class="pf-c-toolbar">
                <div class="pf-c-toolbar__content">
                    ${this.renderSearch()}&nbsp;
                    <div class="pf-c-toolbar__bulk-select">
                        ${this.renderToolbar()}
                    </div>&nbsp;
                    ${this.renderToolbarAfter()}
                    <ak-table-pagination
                        class="pf-c-toolbar__item pf-m-pagination"
                        .pages=${this.data?.pagination}
                        .pageChangeHandler=${(page: number) => {this.page = page; }}>
                    </ak-table-pagination>
                </div>
            </div>
            <table class="pf-c-table pf-m-compact pf-m-grid-md pf-m-expandable">
                <thead>
                    <tr role="row">
                        ${this.expandable ? html`<td role="cell">` : html``}
                        ${this.columns().map((col) => col.render(this))}
                    </tr>
                </thead>
                ${this.data ? this.renderRows() : this.renderLoading()}
            </table>
            <div class="pf-c-pagination pf-m-bottom">
                <ak-table-pagination
                    class="pf-c-toolbar__item pf-m-pagination"
                    .pages=${this.data?.pagination}
                    .pageChangeHandler=${(page: number) => { this.page = page; }}>
                </ak-table-pagination>
            </div>`;
    }

    render(): TemplateResult {
        return this.renderTable();
    }
}

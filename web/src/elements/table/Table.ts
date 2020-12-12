import { gettext } from "django";
import { CSSResult, html, LitElement, property, TemplateResult } from "lit-element";
import { PBResponse } from "../../api/client";
import { COMMON_STYLES } from "../../common/styles";

import "./TablePagination";

export abstract class Table<T> extends LitElement {
    abstract apiEndpoint(page: number): Promise<PBResponse<T>>;
    abstract columns(): Array<string>;
    abstract row(item: T): Array<any>;

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

    @property()
    expandable: boolean = false;

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
        this.apiEndpoint(this.page).then((r) => {
            this.data = r;
            this.page = r.pagination.current;
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

    private renderRows(): TemplateResult[] | undefined {
        if (!this.data) {
            return;
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
                    ${this.renderExpanded(item)}
                </tr>
            </tbody>`;
        });
    }

    renderToolbar(): TemplateResult {
        return html`&nbsp;<button
            @click=${() => { this.fetch(); }}
            class="pf-c-button pf-m-primary">
            ${gettext("Refresh")}
        </button>`;
    }

    renderTable(): TemplateResult {
        if (!this.data) {
            this.fetch();
        }
        return html`<div class="pf-c-toolbar">
                <div class="pf-c-toolbar__content">
                    <div class="pf-c-toolbar__bulk-select">
                        ${this.renderToolbar()}
                    </div>
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
                        ${this.columns().map((col) => html`<th role="columnheader" scope="col">${gettext(col)}</th>`)}
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

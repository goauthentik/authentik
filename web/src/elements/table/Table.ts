import { gettext } from "django";
import { html, LitElement, property, TemplateResult } from "lit-element";
import { PBResponse } from "../../api/client";
import { COMMON_STYLES } from "../../common/styles";

export abstract class Table<T> extends LitElement {
    abstract apiEndpoint(page: number): Promise<PBResponse<T>>;
    abstract columns(): Array<string>;
    abstract row(item: T): Array<string>;

    @property()
    data?: PBResponse<T>;

    @property()
    page = 1;

    static get styles() {
        return [COMMON_STYLES];
    }

    public fetch() {
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
                            <h2 class="pf-c-title pf-m-lg">Loading</h2>
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
        return this.data.results.map((item) => {
            const fullRow = ["<tr role=\"row\">"].concat(
                this.row(item).map((col) => {
                    return `<td role="cell">${col}</td>`;
                })
            );
            fullRow.push("</tr>");
            return html(<any>fullRow);
        });
    }

    renderTable() {
        if (!this.data) {
            this.fetch();
        }
        return html`<div class="pf-c-toolbar">
                <div class="pf-c-toolbar__content">
                    <div class="pf-c-toolbar__bulk-select">
                        <slot name="create-button"></slot>
                        <button
                            @click=${() => {this.fetch();}}
                            class="pf-c-button pf-m-primary"
                        >
                            ${gettext("Refresh")}
                        </button>
                    </div>
                    <pb-table-pagination
                        class="pf-c-toolbar__item pf-m-pagination"
                        .table=${this}
                    ></pb-table-pagination>
                </div>
            </div>
            <table class="pf-c-table pf-m-compact pf-m-grid-md">
                <thead>
                    <tr role="row">
                        ${this.columns().map(
        (col) => html`<th role="columnheader" scope="col">${gettext(col)}</th>`
    )}
                    </tr>
                </thead>
                <tbody role="rowgroup">
                    ${this.data ? this.renderRows() : this.renderLoading()}
                </tbody>
            </table>
            <div class="pf-c-pagination pf-m-bottom">
                <pb-table-pagination
                    class="pf-c-toolbar__item pf-m-pagination"
                    .table=${this}
                ></pb-table-pagination>
            </div>`;
    }

    render() {
        return this.renderTable();
    }
}

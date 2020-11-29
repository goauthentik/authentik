import { html, LitElement, property, TemplateResult } from "lit-element";
import { until } from "lit-html/directives/until.js";
import { PBResponse } from "../../api/client";
import { COMMON_STYLES } from "../../common/styles";

export abstract class Table extends LitElement {
    abstract apiEndpoint(page: number): Promise<PBResponse>;
    abstract columns(): Array<string>;
    abstract row(item: any): Array<string>;

    @property()
    data?: PBResponse;

    @property()
    page: number = 1;

    static get styles() {
        return [COMMON_STYLES];
    }

    public fetch() {
        this.apiEndpoint(this.page).then((r) => {
            this.data = r;
            this.page = r.pagination.current;
        });
    }

    private renderRows(): TemplateResult[] | undefined {
        if (!this.data) {
            return;
        }
        return this.data.results.map((item) => {
            const fullRow = [`<tr role="row">`].concat(
                this.row(item).map((col) => {
                    return `<td role="cell">${col}</td>`;
                })
            );
            fullRow.push(`</tr>`);
            return html(<any>fullRow);
        });
    }

    render() {
        if (!this.data) {
            this.fetch();
            return;
        }
        return html`<div class="pf-c-toolbar">
                <div class="pf-c-toolbar__content">
                    <div class="pf-c-toolbar__bulk-select">
                        <slot name="create-button"></slot>
                        <button
                            @click=${() => {
                                this.fetch();
                            }}
                            class="pf-c-button pf-m-primary"
                        >
                            Refresh
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
                            (col) => html`<th role="columnheader" scope="col">${col}</th>`
                        )}
                    </tr>
                </thead>
                <tbody role="rowgroup">
                    ${this.renderRows()}
                </tbody>
            </table>
            <div class="pf-c-pagination pf-m-bottom">
                <pb-table-pagination
                    class="pf-c-toolbar__item pf-m-pagination"
                    .table=${this}
                ></pb-table-pagination>
            </div>`;
    }
}

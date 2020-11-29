import { html, LitElement } from "lit-element";
import { until } from "lit-html/directives/until.js";
import { PBResponse } from "../api/client";
import { COMMON_STYLES } from "../common/styles";

export abstract class Table extends LitElement {
    abstract apiEndpoint(): Promise<PBResponse>;
    abstract columns(): Array<string>;
    abstract row(item: any): Array<string>;

    private data: PBResponse = <PBResponse>{};

    static get styles() {
        return [COMMON_STYLES];
    }

    private renderRows() {
        return this.apiEndpoint()
            .then((r) => (this.data = r))
            .then(() => {
                return this.data.results.map((item) => {
                    const fullRow = [`<tr role="row">`].concat(
                        this.row(item).map((col) => {
                            return `<td role="cell">${col}</td>`;
                        })
                    );
                    fullRow.push(`</tr>`);
                    return html(<any>fullRow);
                });
            });
    }

    render() {
        return html`<table class="pf-c-table pf-m-compact pf-m-grid-md">
            <thead>
                <tr role="row">
                    ${this.columns().map(
                        (col) => html`<th role="columnheader" scope="col">${col}</th>`
                    )}
                </tr>
            </thead>
            <tbody role="rowgroup">
                ${until(this.renderRows(), html`<tr role="row"><td>loading...</tr></td>`)}
            </tbody>
        </table>`;
    }
}

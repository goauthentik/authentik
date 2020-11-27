import { css, html, LitElement, TemplateResult } from "lit-element";
import { until } from "lit-html/directives/until.js";
import { DefaultClient, PBResponse } from "../api/client";

export abstract class Table extends LitElement {
    abstract apiEndpoint(): string[];
    abstract columns(): Array<string>;
    abstract row(item: any): Array<TemplateResult>;

    private data: PBResponse = <PBResponse>{};

    public static get styles() {
        return css`
            table {
                width: 100%;
            }
            table,
            tr,
            td {
                border: 1px inset white;
                border-collapse: collapse;
            }
            td,
            th {
                padding: 0.5rem;
            }
            td:hover {
                border: 1px solid red;
            }
        `;
    }

    private renderRows() {
        return DefaultClient.fetch<PBResponse>(...this.apiEndpoint())
            .then((r) => (this.data = r))
            .then(() => {
                return this.data.results.map((item) => {
                    return this.row(item).map((col) => {
                        // let t = <TemplateStringsArray>[];
                        return col;
                    });
                });
            });
    }

    render() {
        return html`<table>
            <thead>
                <tr>
                    ${this.columns().map((col) => html`<th>${col}</th>`)}
                </tr>
            </thead>
            <tbody>
                ${until(this.renderRows(), html`<tr><td>loading...</tr></td>`)}
            </tbody>
        </table>`;
    }
}

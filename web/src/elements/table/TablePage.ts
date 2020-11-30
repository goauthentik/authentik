import { html } from "lit-html";
import { Table } from "./Table";

export abstract class TablePage<T> extends Table<T> {
    abstract pageTitle(): string;
    abstract pageDescription(): string;
    abstract pageIcon(): string;

    render() {
        return html`<section class="pf-c-page__main-section pf-m-light">
                <div class="pf-c-content">
                    <h1>
                        <i class="${this.pageIcon()}"></i>
                        ${this.pageTitle()}
                    </h1>
                    <p>${this.pageDescription()}</p>
                </div>
            </section>
            <section class="pf-c-page__main-section pf-m-no-padding-mobile">
                <div class="pf-c-card">${this.renderTable()}</div>
            </section>`;
    }
}

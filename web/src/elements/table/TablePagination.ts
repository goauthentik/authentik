import { customElement, html, LitElement, property } from "lit-element";
import { Table } from "./Table";
import { COMMON_STYLES } from "../../common/styles";

@customElement("pb-table-pagination")
export class TablePagination extends LitElement {
    @property()
    table?: Table;

    static get styles() {
        return [COMMON_STYLES];
    }

    previousHandler() {
        if (!this.table?.data?.pagination.previous) {
            console.debug(`passbook/tables: no previous`);
            return;
        }
        this.table.page = this.table?.data?.pagination.previous;
    }

    nextHandler() {
        if (!this.table?.data?.pagination.next) {
            console.debug(`passbook/tables: no next`);
            return;
        }
        this.table.page = this.table?.data?.pagination.next;
    }

    render() {
        return html` <div class="pf-c-pagination pf-m-compact pf-m-hidden pf-m-visible-on-md">
            <div class="pf-c-pagination pf-m-compact pf-m-compact pf-m-hidden pf-m-visible-on-md">
                <div class="pf-c-options-menu">
                    <div class="pf-c-options-menu__toggle pf-m-text pf-m-plain">
                        <span class="pf-c-options-menu__toggle-text">
                            ${this.table?.data?.pagination.start_index} -
                            ${this.table?.data?.pagination.end_index} of
                            ${this.table?.data?.pagination.count}
                        </span>
                    </div>
                </div>
                <nav class="pf-c-pagination__nav" aria-label="Pagination">
                    <div class="pf-c-pagination__nav-control pf-m-prev">
                        <button
                            class="pf-c-button pf-m-plain"
                            @click=${() => {
                                this.previousHandler();
                            }}
                            disabled="${this.table?.data?.pagination.previous ? "true" : "false"}"
                            aria-label="{% trans 'Go to previous page' %}"
                        >
                            <i class="fas fa-angle-left" aria-hidden="true"></i>
                        </button>
                    </div>
                    <div class="pf-c-pagination__nav-control pf-m-next">
                        <button
                            class="pf-c-button pf-m-plain"
                            @click=${() => {
                                this.nextHandler();
                            }}
                            disabled="${this.table?.data?.pagination.next ? "true" : "false"}"
                            aria-label="{% trans 'Go to next page' %}"
                        >
                            <i class="fas fa-angle-right" aria-hidden="true"></i>
                        </button>
                    </div>
                </nav>
            </div>
        </div>`;
    }
}

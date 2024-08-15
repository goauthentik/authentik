import { bound } from "@goauthentik/elements/decorators/bound";
import { match } from "ts-pattern";

import { html } from "lit";
import { classMap } from "lit/directives/class-map.js";

// Because TableColumn isn't a component, it won't be the dispatch target and it won't have an
// identity beyond the host passed in, so we must include with the event a payload that identifies
// the source TableColumn in some way.
//
export class TableSortEvent extends Event {
    static readonly eventName = "tablesort";
    public value: string;
    constructor(value: string) {
        super(TableSortEvent.eventName, { composed: true, bubbles: true });
        this.value = value;
    }
}

/**
 * class TableColumn
 *
 * This is a helper class for rendering the contents of a table column header.
 *
 * ## Events
 *
 * - @fires tablesort: when the header is clicked, if the host is not undefined
 *
 */
export class TableColumn {
    /**
     * The text to show in the column header
     */
    value: string;

    /**
     * If not undefined, the element that will first receive the `tablesort` event
     */
    host?: HTMLElement;

    /**
     * If not undefined, show the sort indicator, and indicate the sort state
     */
    orderBy?: string;

    constructor(value: string, orderBy?: string, host?: HTMLElement) {
        this.value = value;
        this.orderBy = orderBy;
        if (host) {
            this.host = host;
        }
    }

    @bound
    onSort() {
        if (this.host && this.orderBy) {
            this.host.dispatchEvent(new TableSortEvent(this.orderBy));
        }
    }

    private sortIndicator(orderBy: string) {
        // prettier-ignore
        switch(orderBy) {
            case this.orderBy:       return "fa-long-arrow-alt-down";
            case `-${this.orderBy}`: return "fa-long-arrow-alt-up";
            default:                 return "fa-arrows-alt-v";
        }
    }

    private sortButton(orderBy: string) {
        return html` <button class="pf-c-table__button" @click=${this.onSort}>
            <div class="pf-c-table__button-content">
                <span class="pf-c-table__text">${this.value}</span>
                <span class="pf-c-table__sort-indicator">
                    <i class="fas ${this.sortIndicator(orderBy)}"></i>
                </span>
            </div>
        </button>`;
    }

    public render(orderBy?: string) {
        const isSelected = orderBy === this.orderBy || orderBy === `-${this.orderBy}`;

        const classes = {
            "pf-c-table__sort": !!(this.host && this.orderBy),
            "pf-m-selected": this.host && isSelected,
        };

        return html`<th role="columnheader" scope="col" class="${classMap(classes)}">
            ${orderBy && this.orderBy ? this.sortButton(orderBy) : html`${this.value}`}
        </th>`;
    }
}

declare global {
    interface GlobalEventHandlersEventMap {
        [TableSortEvent.eventName]: TableSortEvent;
    }
}

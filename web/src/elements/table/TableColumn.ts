import { bound } from "@goauthentik/elements/decorators/bound";
import { match } from "ts-pattern";

import { html } from "lit";
import { classMap } from "lit/directives/class-map.js";

export enum SortBy {
    None,
    Up,
    Down,
}

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
     * If not undefined, show the sort indicator, and indicate the sort state described
     */
    orderBy?: SortBy;

    constructor(value: string, orderBy?: SortBy, host?: HTMLElement) {
        this.value = value;
        this.orderBy = orderBy;
        if (host) {
            this.host = host;
        }
    }

    @bound
    onSort() {
        if (this.host) {
            this.host.dispatchEvent(new TableSortEvent(this.value));
        }
    }

    private get sortIndicator() {
        return match(this.orderBy)
            .with(SortBy.None, () => "fa-arrows-alt-v")
            .with(SortBy.Up, () => "fa-long-arrow-alt-up")
            .with(SortBy.Down, () => "fa-long-arrow-alt-down")
            .otherwise(() => "");
    }

    private get sortButton() {
        return html` <button class="pf-c-table__button" @click=${this.onSort}>
            <div class="pf-c-table__button-content">
                <span class="pf-c-table__text">${this.value}</span>
                <span class="pf-c-table__sort-indicator">
                    <i class="fas ${this.sortIndicator}"></i>
                </span>
            </div>
        </button>`;
    }

    render() {
        const classes = {
            "pf-c-table__sort": !!this.orderBy,
            "pf-m-selected": this.orderBy && this.orderBy !== SortBy.None,
        };

        return html`<th role="columnheader" scope="col" class="${classMap(classes)}">
            ${this.orderBy ? this.sortButton : html`${this.value}`}
        </th>`;
    }
}

declare global {
    interface GlobalEventHandlersEventMap {
        [TableSortEvent.eventName]: TableSortEvent;
    }
}

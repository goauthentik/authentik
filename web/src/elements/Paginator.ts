/**
 * @file Barrel file and default registry ('ak-paginator') for the Paginator component
 */

import {
    toPaginator,
    pageBounds,
    PaginatorPageBounds,
    PaginatorState,
} from "./Paginator_impl/bounds";
import { PageChangeEvent } from "./Paginator_impl/events";
import { Paginator } from "./Paginator_impl/Paginator";

export {
    Paginator,
    PageChangeEvent,
    toPaginator,
    pageBounds,
    type PaginatorPageBounds,
    type PaginatorState,
};

window.customElements.define("ak-paginator", Paginator);

declare global {
    interface HTMLElementTagNameMap {
        "ak-paginator": Paginator;
    }
}

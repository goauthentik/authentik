/**
 * @file Barrel file and default registry ('ak-paginator') for the Paginator component
 */

import { Paginator } from "./Paginator_impl/Paginator";
import { PageChangeEvent } from "./Paginator_impl/events";

export { Paginator, PageChangeEvent };

window.customElements.define("ak-paginator", Paginator);

declare global {
    interface HTMLElementTagNameMap {
        "ak-paginator": Paginator;
    }
}

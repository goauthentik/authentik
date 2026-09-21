/**
 * @file Barrel file and default registry ('ak-paginator') for the Paginator component
 */

import { PageChangeEvent } from "./Paginator_impl/events";
import { Paginator } from "./Paginator_impl/Paginator";

export { Paginator, PageChangeEvent };

window.customElements.define("ak-paginator", Paginator);

declare global {
    interface HTMLElementTagNameMap {
        "ak-paginator": Paginator;
    }
}

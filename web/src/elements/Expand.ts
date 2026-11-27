/**
 * @file Barrel file and default registry ('ak-expand') for the Expand component
 */

import { akExpand, Expand, type ExpandProps } from "./Expand_impl/Expand";

export { akExpand, Expand };
export type { ExpandProps };

window.customElements.define("ak-expand", Expand);

declare global {
    interface HTMLElementTagNameMap {
        "ak-expand": Expand;
    }
}

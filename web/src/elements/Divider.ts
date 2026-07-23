/**
 * @file Barrel file and default registry ('ak-divider') for the Divider component
 */

import { akDivider, Divider, type DividerProps } from "./Divider_impl/Divider";

export { akDivider, Divider };
export type { DividerProps };

window.customElements.define("ak-divider", Divider);

declare global {
    interface HTMLElementTagNameMap {
        "ak-divider": Divider;
    }
}

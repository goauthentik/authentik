/**
 * @file Barrel file and default registry ('ak-expansion-toggle') for the ExpansionToggle component
 */

import {
    akExpansionToggle,
    ExpansionToggle,
    type ExpansionToggleProps,
} from "./ExpansionToggle_impl/ExpansionToggle";

export { akExpansionToggle, ExpansionToggle };
export type { ExpansionToggleProps };

window.customElements.define("ak-expansion-toggle", ExpansionToggle);

declare global {
    interface HTMLElementTagNameMap {
        "ak-expansion-toggle": ExpansionToggle;
    }
}

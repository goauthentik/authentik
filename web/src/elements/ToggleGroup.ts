/**
 * @file Barrel file and default registry ('ak-toggle-group') for the ToggleGroup component
 */

import { ToggleGroup, ToggleGroupEvent } from "./ToggleGroup_impl/ToggleGroup";

export { ToggleGroup, ToggleGroupEvent };

window.customElements.define("ak-toggle-group", ToggleGroup);

declare global {
    interface HTMLElementTagNameMap {
        "ak-toggle-group": ToggleGroup;
    }
}

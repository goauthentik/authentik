/**
 * @file Barrel file and default registry ('ak-label') for the Label component
 */

import { akLabel, Label, type LabelProps } from "./Label_impl/Label";

export { akLabel, Label };
export type { LabelProps };

window.customElements.define("ak-label", Label);

declare global {
    interface HTMLElementTagNameMap {
        "ak-label": Label;
    }
}

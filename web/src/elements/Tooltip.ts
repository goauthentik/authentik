/**
 * @file Barrel file and default registry ('ak-tooltip') for the Tooltip component
 */

import { Tooltip, type Trigger } from "./Tooltip_impl/Tooltip";
import { akTooltip, type TooltipProps } from "./Tooltip_impl/Tooltip.builder";

export { akTooltip, Tooltip, type TooltipProps, type Trigger };

window.customElements.define("ak-tooltip", Tooltip);

declare global {
    interface HTMLElementTagNameMap {
        "ak-tooltip": Tooltip;
    }
}

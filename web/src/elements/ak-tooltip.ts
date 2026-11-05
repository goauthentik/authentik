/**
 * @file Barrel file and default registry ('ak-tooltip') for the Tooltip component
 */

import { Tooltip, type Trigger } from "./Tooltip/Tooltip";
import { akTooltip, type TooltipProps } from "./Tooltip/Tooltip.builder";
import { TooltipWithHover } from "./Tooltip/Tooltip.debug";
window.customElements.define("ak-tooltip", TooltipWithHover(Tooltip));

export { akTooltip, Tooltip, type TooltipProps, type Trigger };

// window.customElements.define("ak-tooltip", Tooltip);

declare global {
    interface HTMLElementTagNameMap {
        "ak-tooltip": Tooltip;
    }
}

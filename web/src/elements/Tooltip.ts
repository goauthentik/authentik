import { Tooltip, type Trigger } from "./Tooltip_impl/Tooltip";
import { akTooltip, type TooltipProps } from "./Tooltip_impl/Tooltip.builder";
import { TooltipWithHover } from "./Tooltip_impl/Tooltip.debug";

export { akTooltip, Tooltip, type TooltipProps, type Trigger };
window.customElements.define("ak-tooltip", TooltipWithHover(Tooltip));

// window.customElements.define("ak-tooltip", Tooltip);

declare global {
    interface HTMLElementTagNameMap {
        "ak-tooltip": Tooltip;
    }
}

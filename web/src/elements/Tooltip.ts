import { Tooltip } from "./Tooltip_impl/Tooltip";
import { akTooltip, type TooltipProps } from "./Tooltip_impl/Tooltip.builder";

export { akTooltip, Tooltip, type TooltipProps };

window.customElements.define("ak-tooltip", Tooltip);

declare global {
    interface HTMLElementTagNameMap {
        "ak-tooltip": Tooltip;
    }
}

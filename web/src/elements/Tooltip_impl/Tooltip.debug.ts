/**
 * @file Alternative implementation of Tooltip that can assist with debugging.
 */

import type { Tooltip } from "./Tooltip";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Constructor<T = Record<string, unknown>> = new (...args: any[]) => T;
type TooltipConstructor<T extends Tooltip = Tooltip> = Constructor<T>;
type TooltipWithHoverType<Base extends TooltipConstructor> = Base & TooltipConstructor<Tooltip>;

const validHtmlID = /^[A-Za-z][.\w\-:]*$/;

/**
 * This mixin replaces the `attachToAnchor` function, which uses mouseenter and mouseleave events to
 * track hover, with a literal "watching for hover" condition, which polls the CSS state of the
 * component for `:hover` 20 times a second. This is hideously inefficient, but it allows DevTools
 * to set the `:hov` pseudo-pseudo-class and keep the tooltip on the screen.
 *
 * To use this, import this module into the barrel file `Tooltip.ts` and replace the
 * customElements call with:
 *
 * ```ts
 * import { TooltipWithHover } from "./Tooltip_impl/Tooltip.debug";
 * window.customElements.define("ak-tooltip", TooltipWithHover(Tooltip));
 * ```
 */
export function TooltipWithHover<Base extends TooltipConstructor>(Superclass: Base) {
    class TooltipWithHover extends Superclass {
        protected hoverCheckInterval = -1;

        protected override attachToAnchor() {
            this.anchor = null;

            if (!this.htmlFor) {
                console.warn("ak-tooltip: tooltip without anchor declared.");
                return;
            }
            const parent = this.getRootNode() as ParentNode;
            if (
                !(
                    parent === document ||
                    parent instanceof HTMLElement ||
                    parent instanceof ShadowRoot
                )
            ) {
                console.warn("ak-tooltip: component not running in a valid context");

                return;
            }

            // Fallback to search based on selector, even if we're pretty sure it's an ID.
            const anchor = validHtmlID.test(this.htmlFor)
                ? parent.querySelector(`#${this.htmlFor}`) || parent.querySelector(this.htmlFor)
                : parent.querySelector(this.htmlFor);

            if (!anchor) {
                console.warn("ak-tooltip: could not find anchor");

                return;
            }

            if (!(anchor instanceof HTMLElement)) {
                console.warn(
                    `ak-tooltip: element '${this.htmlFor}' does not resolve to an HTMLElement`,
                );

                return;
            }

            this.anchor = anchor;

            this.hoverCheckInterval = self.setInterval(() => {
                const anchorHovered = this.anchor?.matches(":hover") ?? false;
                const tooltipHovered = this.dialog.value?.matches(":hover") ?? false;

                // Transition based on hover state
                const currentlyHovering = anchorHovered || tooltipHovered;
                const wasHovering = this.state.type !== "tooltip-hidden";

                if (currentlyHovering && !wasHovering) {
                    this.onAnchorEnter();
                } else if (!currentlyHovering && wasHovering) {
                    this.onAnchorLeave();
                }
            }, 50);
        }

        public override disconnectedCallback() {
            super.disconnectedCallback();
            clearInterval(this.hoverCheckInterval);
        }
    }

    return TooltipWithHover as TooltipWithHoverType<Base>;
}

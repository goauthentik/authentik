/**
 * @file Implementation code for the Tooltip component
 */

import { parseLength } from "../utils/parseSize.js";
import { TooltipInitialState, type TooltipState } from "./StateMachine";
import Styles from "./Tooltip.styles";

import type { Middleware, Placement } from "@floating-ui/dom";
import { autoUpdate, computePosition, flip, offset, shift } from "@floating-ui/dom";

import { html, LitElement, nothing, PropertyValues } from "lit";
import { property, query } from "lit/decorators.js";
import { createRef, ref, Ref } from "lit/directives/ref.js";

export type Trigger = "hover" | "focus";

const DEFAULT_SHOW_DELAY = "100ms";
const DEFAULT_HIDE_DELAY = "150ms";

const delaySyntax = /^(\d+)\s*(ms|s)$/;

function parseDelay(delay: string) {
    const g = delaySyntax.exec(delay.trim());
    if (!(g && g.length > 2)) {
        return 0;
    }
    return parseInt(g[1], 10) * (g[2] === "ms" ? 1 : 1000);
}

/**
 * A tooltip displays additional information when users hover over or focus on an anchor element
 * in order to provide context or to provide a textual label for icons and pictograms. Think
 * of a tooltip as an extra label that can be made to appear near an HTMLElement that may require
 * additional clarification.
 *
 * ## Attributes
 *
 * Just like a `label`, there are two ways to specify the component with which a tooltip will be
 * associated. Unlike HTMLLabelElement, you can set these to any HTMLElement, not just
 * HTMLFormElement controls.
 *
 * - @attr {string} for - Like a `<label>`, the ID (or selector) of a sibling element which the
 *   tooltip will appear nearby. or:<
 * - @property {HTMLElement} target - A direct reference to the anchor element. Takes precedence over
 *   "for" attribute. Unlike HTMLLabelElement.control, this property is read/write. If both are set,
 *   `target` takes precendence. Other attributes:
 * - @attr {"hover"|"focus"} trigger - Event type that triggers tooltip display (default: "hover")
 * - "hover": Shows on mouseenter/mouseleave events
 * - "focus": Shows on focus/blur events
 * - @attr {Placement} placement - Positioning relative to anchor: "top", "top-start", "top-end",
 *   "right", "right-start", "right-end", "bottom", "bottom-start", "bottom-end", "left",
 *   "left-start", "left-end" (default: "top")
 * - @attr {boolean} hide-arrow - Don't show the arrow
 *
 * ### Deprecated attributes (try not to use these):
 *
 * - @attr {string} content - Text content of the tooltip. DEPRECATED: prefer using the slot
 *
 * ## Slots
 *
 * @class Tooltip
 * @element ak-tooltip
 *
 * @summary A **tooltip** is a an element that appears on hover to provide additional information
 *
 * @slot - Slot for tooltip content. Anonymous, no `slot` attribute required. Prefer using this
 * over the `content` attribute.
 *
 * ## Component elements that can be customized via the `::part()` pseudo-selector
 *
 * @csspart tooltip - The dialog element containing the tooltip
 * @csspart arrow - The arrow element pointing toward the anchor
 * @csspart content - The content wrapper element inside the tooltip
 */
export class Tooltip extends LitElement {
    public static readonly styles = [Styles];

    /**
     * @deprecated prefer using slots.
     * @attr {string} content: What to show in the tooltip
     */
    @property({ type: String })
    public content = "";

    /**
     * @attr {boolean} hideArrow: Don't show an arrow pointing toward the tooltip.
     */
    @property({ type: Boolean, attribute: "hide-arrow" })
    public hideArrow = false;

    /**
     * @attr {string} trigger - What event causes the tooltip to show up.
     */
    @property({ type: String })
    public trigger: Trigger = "hover";

    /**
     * @attr { string } placement - Where should we place the tooltip?
     */
    @property({ type: String })
    public placement: Placement = "top";

    @property({ type: Boolean, reflect: true })
    public expanded = false;

    protected state: TooltipState = new TooltipInitialState(this);

    protected dialog: Ref<HTMLDialogElement> = createRef();

    @query('[part="arrow"]')
    private arrow?: HTMLElement;

    public showDelay = parseDelay(DEFAULT_SHOW_DELAY);
    public hideDelay = parseDelay(DEFAULT_HIDE_DELAY);

    #cleanupFloating?: () => void;
    #anchorAbortController = new AbortController();

    public setState(state: TooltipState) {
        this.state = state;
    }

    // To enable the debugging variant, these cannot be made private.
    protected onAnchorEnter = () => {
        this.state.onAnchorEnter();
    };

    protected onAnchorLeave = () => {
        this.state.onAnchorLeave();
    };

    #detachFromAnchor() {
        this.#anchorAbortController.abort();
        this.#anchorAbortController = new AbortController();

        this.state.clearTimeout();
        this.#cleanupFloating?.();
    }

    public override connectedCallback() {
        super.connectedCallback();

        const signal = { signal: this.#anchorAbortController.signal };
        this.addEventListener("focusin", this.onAnchorEnter, signal);
        this.addEventListener("focusout", this.onAnchorLeave, signal);
        if (this.trigger === "hover") {
            this.addEventListener("mouseenter", this.onAnchorEnter, signal);
            this.addEventListener("touchstart", this.onAnchorEnter, signal);
            this.addEventListener("mouseleave", this.onAnchorLeave, signal);
            this.addEventListener("touchend", this.onAnchorLeave, signal);
        }
    }

    public override disconnectedCallback() {
        super.disconnectedCallback();
        this.#detachFromAnchor();
    }

    public override willUpdate(changed: PropertyValues<this>) {
        super.willUpdate(changed);
        this.hideDelay = parseDelay(
            getComputedStyle(this)?.getPropertyValue("--ak-c-tooltip--HideDelay") ??
                DEFAULT_HIDE_DELAY,
        );
        this.showDelay = parseDelay(
            getComputedStyle(this)?.getPropertyValue("--ak-c-tooltip--ShowDelay") ??
                DEFAULT_SHOW_DELAY,
        );
    }

    public override render() {
        const fromSlot = this.textContent?.trim() || this.childNodes.length > 0;
        return html` <div part="container">
            <div part="content" role="tooltip" aria-labelledby="tooltip">
                <slot
                    id="content"
                    @slotchange=${() => {
                        this.requestUpdate();
                    }}
                ></slot>
            </div>
            <dialog
                ${ref(this.dialog)}
                id="tooltip"
                part="tooltip"
                role="tooltip"
                tabindex="-1"
                ?inert=${!open}
            >
                ${this.hideArrow ? nothing : html`<div part="arrow"></div>`}
                <div part="tooltip-body">
                    <slot name="tooltip">${this.content}</slot>
                </div>
            </dialog>
        </div>`;
    }

    #updatePosition = async () => {
        const offsetDistance = parseLength(
            getComputedStyle(this).getPropertyValue("--ak-c-tooltip--Offset"),
        );

        const dialog = this.dialog.value;
        if (!dialog) {
            return;
        }

        const middleware: Middleware[] = [offset(offsetDistance), flip(), shift()];
        const { x, y, placement } = await computePosition(this, dialog, {
            placement: this.placement,
            middleware,
        });

        Object.assign(dialog.style, {
            left: `${x}px`,
            top: `${y}px`,
        });

        if (this.arrow && !this.hideArrow) {
            this.arrow.classList.remove(...this.arrow.classList);
            this.arrow.classList.add(`m-${placement}`);
        }
    };

    #setPositioning() {
        const dialog = this.dialog.value;
        if (!dialog) {
            return;
        }

        this.#cleanupFloating = autoUpdate(this, dialog, this.#updatePosition, {
            ancestorScroll: true,
            ancestorResize: true,
            elementResize: true,
            layoutShift: true,
        });
    }

    #showTooltip() {
        const dialog = this.dialog.value;
        if (!dialog) {
            return;
        }

        dialog.inert = true;
        dialog.show();
        dialog.inert = false;
    }

    #hideTooltip() {
        const dialog = this.dialog.value;
        if (!dialog) {
            return;
        }
        dialog.close();
    }

    public override updated(changed: PropertyValues<this>) {
        if (changed.has("expanded")) {
            if (this.expanded) {
                this.#setPositioning();
                this.#showTooltip();
            } else {
                this.#hideTooltip();
            }
        }
    }
}

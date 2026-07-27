import { getDeepActiveElement } from "../utils/getDeepActiveElement.js";
import { findNearestSibling } from "../utils/nearestSibling.js";
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

const validHtmlId = /^[A-Za-z][.\w\-:]*$/;
const delaySyntax = /^(\d+)\s*(ms|s)$/;

function parseDelay(delay: string) {
    const g = delaySyntax.exec(delay.trim());
    if (!(g && g.length > 2)) {
        return 0;
    }
    return parseInt(g[1], 10) * (g[2] === "ms" ? 1 : 1000);
}

/**
 * @class Tooltip
 * @element ak-tooltip
 *
 * @summary A **tooltip** is a an element that appears on hover to provide additional information
 *
 * @description
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
 *   tooltip will appear nearby.
 *
 * or:
 *
 * - @property {HTMLElement} target - A direct reference to the anchor element. Takes precedence over
 *   "for" attribute. Unlike HTMLLabelElement.control, this property is read/write.
 *
 * If both are set, `target` takes precendence.
 *
 * Other attributes:
 *
 * - @attr {"hover"|"focus"} trigger - Event type that triggers tooltip display (default: "hover")
 *   - "hover": Shows on mouseenter/mouseleave events
 *   - "focus": Shows on focus/blur events
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
 * @slot - Slot for tooltip content. Anonymous, no `slot` attribute required. Prefer using this
 * over the `content` attribute.
 *
 * ## Component elements that can be customized via the `::part()` pseudo-selector
 *
 * @csspart tooltip - The dialog element containing the tooltip
 * @csspart arrow - The arrow element pointing toward the anchor
 * @csspart content - The content wrapper element inside the tooltip
 *
 */
export class Tooltip extends LitElement {
    static readonly styles = [Styles];

    /**
     * @attr {string} content: What to show in the tooltip
     *
     * @deprecated prefer using slots.
     */
    @property({ type: String })
    public content = "";

    /**
     * @attr {boolean} hideArrow: Don't show an arrow pointing toward the tooltip.
     */
    @property({ type: Boolean, attribute: "hide-arrow" })
    public hideArrow = false;

    /**
     * @attr {string} for: The id or selector for the target. Must be in the same context as the
     * tooltip.
     */
    @property({ type: String, attribute: "for" })
    public htmlFor = "";

    /**
     * @attr {object} target: A reference to the target. Must be in the same or in a sibling context
       of the tooltip.  `.target` takes precedence over `for`
     */
    @property({ type: Object })
    public target?: HTMLElement;

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

    protected anchor: HTMLElement | null = null;

    #cleanupFloating?: () => void;
    #anchorAbortController = new AbortController();
    #tooltipAbortController = new AbortController();

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

    #onTooltipEnter = () => {
        this.state.onTooltipEnter();
    };

    #onTooltipLeave = () => {
        this.state.onTooltipLeave();
    };

    #getAnchor() {
        const parent = this.getRootNode() as ParentNode;
        if (
            !(parent === document || parent instanceof HTMLElement || parent instanceof ShadowRoot)
        ) {
            console.warn("ak-tooltip: component not running in a valid context");
            return null;
        }

        if (!(this.htmlFor || this.target)) {
            console.warn("ak-tooltip: tooltip without anchor declared.");
            return null;
        }

        if (this.target) {
            if (!(this.target instanceof HTMLElement)) {
                console.warn("ak-tooltip: '.target' prop does not resolve to an HTMLElement");
                return null;
            }
            return this.target;
        }

        // Fallback to search based on selector, even if we're pretty sure it's an ID.
        const anchor = validHtmlId.test(this.htmlFor)
            ? parent.querySelector(`#${this.htmlFor}`) ||
              findNearestSibling(this, this.htmlFor) ||
              parent.querySelector(this.htmlFor)
            : findNearestSibling(this, this.htmlFor) || parent.querySelector(this.htmlFor);

        if (!anchor) {
            console.warn("ak-tooltip: could not find anchor");
            return null;
        }

        if (!(anchor instanceof HTMLElement)) {
            console.warn(
                `ak-tooltip: element '${this.htmlFor}' does not resolve to an HTMLElement`
            );
            return null;
        }

        return anchor;
    }

    protected attachToAnchor() {
        this.anchor = this.#getAnchor();
        if (!this.anchor) {
            return;
        }

        const signal = { signal: this.#anchorAbortController.signal };
        this.anchor.addEventListener("focus", this.onAnchorEnter, signal);
        this.anchor.addEventListener("blur", this.onAnchorLeave, signal);
        if (this.trigger === "hover") {
            this.anchor.addEventListener("mouseenter", this.onAnchorEnter, signal);
            this.anchor.addEventListener("touchstart", this.onAnchorEnter, signal);
            this.anchor.addEventListener("mouseleave", this.onAnchorLeave, signal);
            this.anchor.addEventListener("touchend", this.onAnchorLeave, signal);
        }
    }

    #detachFromAnchor() {
        if (this.expanded) {
            this.#detachDialogListeners();
        }
        if (this.anchor) {
            this.#anchorAbortController.abort();
            this.#anchorAbortController = new AbortController();
        }
        this.state.clearTimeout();
        this.#cleanupFloating?.();
    }

    public override connectedCallback() {
        super.connectedCallback();

        // `connectedCallback()` is run when the *opening* tag is parsed, not the entire component.
        // Calling `attachToAnchor` at the end of the current task queue allows the browser to
        // finishing parsing the tooltip and its anchor, which in turns allows the tooltip to find
        // its anchor even if the anchor is a later sibling.
        requestAnimationFrame(() => this.attachToAnchor());
    }

    public override disconnectedCallback() {
        super.disconnectedCallback();
        this.#detachFromAnchor();
    }

    public override willUpdate(changed: PropertyValues<this>) {
        super.willUpdate(changed);
        this.hideDelay = parseDelay(
            getComputedStyle(this)?.getPropertyValue("--ak-c-tooltip--HideDelay") ??
                DEFAULT_HIDE_DELAY
        );
        this.showDelay = parseDelay(
            getComputedStyle(this)?.getPropertyValue("--ak-c-tooltip--ShowDelay") ??
                DEFAULT_SHOW_DELAY
        );
    }

    public override render() {
        const fromSlot = this.textContent?.trim() || this.childNodes.length > 0;
        const content = fromSlot ? html`<slot></slot>` : this.content;
        return html`<dialog
            ${ref(this.dialog)}
            part="tooltip"
            role="tooltip"
            tabindex="-1"
            aria-live="polite"
        >
            ${this.hideArrow ? nothing : html`<div part="arrow"></div>`}
            <div part="content">${content}</div>
        </dialog>`;
    }

    #attachDialogListeners() {
        if (!this.expanded) {
            throw new Error("Can't happen.");
        }

        const signal = { signal: this.#tooltipAbortController.signal };
        this.dialog.value?.addEventListener("focus", this.#onTooltipEnter, signal);
        this.dialog.value?.addEventListener("blur", this.#onTooltipLeave, signal);
        if (this.trigger === "hover") {
            this.dialog.value?.addEventListener("mouseenter", this.#onTooltipEnter, signal);
            this.dialog.value?.addEventListener("mouseleave", this.#onTooltipLeave, signal);
            this.dialog.value?.addEventListener("touchstart", this.#onTooltipEnter, signal);
            this.dialog.value?.addEventListener("touchend", this.#onTooltipLeave, signal);
        }
    }

    #detachDialogListeners() {
        this.#tooltipAbortController.abort();
        this.#tooltipAbortController = new AbortController();
    }

    #updatePosition = async () => {
        const offsetDistance = parseLength(
            getComputedStyle(this).getPropertyValue("--ak-c-tooltip--Offset")
        );

        const [anchor, dialog] = [this.anchor, this.dialog.value];
        if (!(anchor && dialog)) {
            return;
        }

        const middleware: Middleware[] = [offset(offsetDistance), flip(), shift()];

        const { x, y, placement, middlewareData } = await computePosition(anchor, dialog, {
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
        const [anchor, dialog] = [this.anchor, this.dialog.value];
        if (!(anchor && dialog)) {
            return;
        }

        this.#cleanupFloating = autoUpdate(anchor, dialog, this.#updatePosition, {
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

        const elementWithFocus = getDeepActiveElement();
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
        if (changed.has("htmlFor")) {
            this.#detachFromAnchor();
            this.attachToAnchor();
        }

        if (changed.has("expanded")) {
            if (this.expanded) {
                this.#attachDialogListeners();
                this.#setPositioning();
                this.#showTooltip();
            } else {
                this.#detachDialogListeners();
                this.#hideTooltip();
            }
        }
    }
}

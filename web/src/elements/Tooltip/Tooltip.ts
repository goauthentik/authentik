/**
 * @file Implementation code for the Tooltip component
 */

import { PopoverSupported } from "../dialogs/positioning.js";
import { parseLength } from "../utils/parseSize.js";
import { TooltipInitialState, type TooltipState } from "./StateMachine";
import Styles from "./Tooltip.styles";

import { IDGenerator } from "@goauthentik/core/id";

import type { Middleware, Placement } from "@floating-ui/dom";
import { autoUpdate, computePosition, flip, offset, shift } from "@floating-ui/dom";

import { html, LitElement, nothing, PropertyValues, TemplateResult } from "lit";
import { property, query } from "lit/decorators.js";
import { createRef, ref, Ref } from "lit/directives/ref.js";

export type Trigger = "hover" | "focus";

const DEFAULT_SHOW_DELAY = "100ms";
const DEFAULT_HIDE_DELAY = "150ms";
const DEFAULT_OFFSET = "0.4rem";

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
 * - @attr {"hover"|"focus"} trigger - Event that triggers tooltip display (default: "hover")
 *
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
 * @class Tooltip
 * @element ak-tooltip
 *
 * @summary A **tooltip** is a an element that appears on hover to provide additional information
 *
 * @slot - The anchor: the element the tooltip decorates. The first slotted element receives
 *   `aria-describedby` pointing at the tooltip content, so it should be the focusable element
 *   itself, not a wrapper around it.
 * @slot tooltip - The tooltip content. Elements without an id will be assigned one. Prefer using
 *   this over the `content` attribute. For an icon-only anchor whose tooltip is its label, point
 *   the anchor's `aria-labelledby` at the slotted element instead of setting `aria-label`, so
 *   readers will only announce it once.
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

    /**
     * The floating element. Uses the PopOver API when possible, otherwise uses a non-modal
     * `<dialog>`. The last will not escape an `overflow: hidden`, but CanIUse says that as of
     * 2026-11 it's 93% available.
     *
     * @expires 2027-07
     */
    protected dialog: Ref<HTMLElement> = createRef();

    @query('[part="arrow"]')
    private arrow?: HTMLElement;

    public showDelay = parseDelay(DEFAULT_SHOW_DELAY);
    public hideDelay = parseDelay(DEFAULT_HIDE_DELAY);

    #cleanupFloating?: () => void;
    #anchorAbortController = new AbortController();

    /** The anchor we last described, and the IDREFs we added to it, so we can undo exactly that. */
    #describedAnchor: Element | null = null;
    #descriptionIDs: string[] = [];
    #setAriaDescription = false;

    #unlinkDescription() {
        const anchor = this.#describedAnchor;

        if (anchor) {
            const remaining = (anchor.getAttribute("aria-describedby") ?? "")
                .split(/\s+/)
                .filter((token) => token && !this.#descriptionIDs.includes(token));

            if (remaining.length) {
                anchor.setAttribute("aria-describedby", remaining.join(" "));
            } else {
                anchor.removeAttribute("aria-describedby");
            }

            if (this.#setAriaDescription) {
                anchor.removeAttribute("aria-description");
            }
        }

        this.#describedAnchor = null;
        this.#descriptionIDs = [];
        this.#setAriaDescription = false;
    }

    #linkDescription = () => {
        this.#unlinkDescription();

        if (!this.isConnected) return;

        const assigned = (name?: string) =>
            this.renderRoot
                .querySelector<HTMLSlotElement>(name ? `slot[name="${name}"]` : "slot:not([name])")
                ?.assignedElements({ flatten: true }) ?? [];

        // A text-only anchor has no element to carry the attribute; nothing to link.
        const [anchor] = assigned();

        if (!anchor) return;

        const content = assigned("tooltip");

        this.#describedAnchor = anchor;

        if (!content.length) {
            // the `content` attribute (deprecated) renders inside our shadow root, so it falls back
            // to ARIA 1.3 `aria-description`. Drop with `content`.
            if (this.content && !anchor.hasAttribute("aria-description")) {
                anchor.setAttribute("aria-description", this.content);
                this.#setAriaDescription = true;
            }

            return;
        }

        const tokens = (anchor.getAttribute("aria-describedby") ?? "").split(/\s+/).filter(Boolean);
        const labelledBy = (anchor.getAttribute("aria-labelledby") ?? "").split(/\s+/);

        for (const element of content) {
            // Don't duplicate the anchor's name in its description label.
            if (element.id && labelledBy.includes(element.id)) continue;

            element.id ||= IDGenerator.elementID();

            if (!tokens.includes(element.id)) {
                tokens.push(element.id);
                this.#descriptionIDs.push(element.id);
            }
        }

        if (this.#descriptionIDs.length) {
            anchor.setAttribute("aria-describedby", tokens.join(" "));
        }
    };

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

    protected onKeyDown = (event: KeyboardEvent) => {
        if (event.key !== "Escape" || event.isComposing) return;

        if (this.state.onEscape()) {
            // Dismiss the tooltip only; a second Escape reaches e.g. an enclosing modal.
            event.preventDefault();
            event.stopPropagation();
        }
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

        window.addEventListener("keydown", this.onKeyDown, { ...signal, capture: true });

        if (this.hasUpdated) this.#linkDescription();
    }

    public override disconnectedCallback() {
        super.disconnectedCallback();
        this.#detachFromAnchor();
        this.#unlinkDescription();
    }

    public override willUpdate(changed: PropertyValues<this>) {
        super.willUpdate(changed);
        const styles = getComputedStyle(this);

        this.hideDelay = parseDelay(
            styles.getPropertyValue("--ak-c-tooltip--HideDelay") || DEFAULT_HIDE_DELAY,
        );

        this.showDelay = parseDelay(
            styles.getPropertyValue("--ak-c-tooltip--ShowDelay") || DEFAULT_SHOW_DELAY,
        );
    }

    protected renderTooltipBody(): TemplateResult {
        return html`${this.hideArrow ? nothing : html`<div part="arrow"></div>`}
            <div part="tooltip-body">
                <slot name="tooltip" @slotchange=${this.#linkDescription}>${this.content}</slot>
            </div>`;
    }

    public override render() {
        const tooltip = PopoverSupported
            ? html`<div
                  ${ref(this.dialog)}
                  id="tooltip"
                  part="tooltip"
                  role="tooltip"
                  popover="manual"
              >
                  ${this.renderTooltipBody()}
              </div>`
            : html`<dialog
                  ${ref(this.dialog)}
                  id="tooltip"
                  part="tooltip"
                  role="tooltip"
                  tabindex="-1"
                  ?inert=${!this.expanded}
              >
                  ${this.renderTooltipBody()}
              </dialog>`;

        return html`<div part="container">
            <div part="content"><slot @slotchange=${this.#linkDescription}></slot></div>
            ${tooltip}
        </div>`;
    }

    #updatePosition = async () => {
        const offsetDistance = parseLength(
            getComputedStyle(this).getPropertyValue("--ak-c-tooltip--Offset") || DEFAULT_OFFSET,
        );

        const dialog = this.dialog.value;

        if (!dialog) {
            return;
        }

        const middleware: Middleware[] = [offset(offsetDistance), flip(), shift()];
        const strategy = PopoverSupported ? "fixed" : "absolute";

        const { x, y, placement } = await computePosition(this, dialog, {
            placement: this.placement,
            strategy,
            middleware,
        });

        Object.assign(dialog.style, {
            position: strategy,
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

        this.#cleanupFloating?.();

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

        if (PopoverSupported) {
            dialog.showPopover();

            return;
        }

        // Without an "inert sandwich", dialog will grab the focus, which we don't want.
        dialog.inert = true;
        (dialog as HTMLDialogElement).show();
        dialog.inert = false;
    }

    #hideTooltip() {
        const dialog = this.dialog.value;

        if (!dialog) {
            return;
        }

        this.#cleanupFloating?.();
        this.#cleanupFloating = undefined;

        if (PopoverSupported) {
            dialog.hidePopover();

            return;
        }

        (dialog as HTMLDialogElement).close();
    }

    public override updated(changed: PropertyValues<this>) {
        if (changed.has("content")) {
            this.#linkDescription();
        }

        if (changed.has("expanded")) {
            if (this.expanded) {
                // Show first: positioning a display:none element measures it as 0x0.
                this.#showTooltip();
                this.#setPositioning();
            } else {
                this.#hideTooltip();
            }
        }
    }
}

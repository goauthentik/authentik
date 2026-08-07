import type { ListSelect } from "#elements/ak-list-select/ak-list-select";
import { findScrollableAncestor, placeAnchoredPopover } from "#elements/dialogs/positioning";

import type { ReactiveController, ReactiveControllerHost } from "lit";

const DEFAULT_REFOCUS_DELAY = 250;

interface SearchSelectMenuHost extends ReactiveControllerHost, HTMLElement {
    open: boolean;
    readOnly: boolean;
}

type ElementGetter<T extends HTMLElement> = () => T | undefined;

/** Owns popover visibility, positioning, and scroll behavior for a search-select menu. */
export class SearchSelectMenuController implements ReactiveController {
    #anchorObserver?: IntersectionObserver;
    /** Timestamp of the last browser-driven popover close (see reopen guard). */
    #lastLightDismiss = -Infinity;
    #reflowFrame?: number;

    constructor(
        private readonly host: SearchSelectMenuHost,
        private readonly getInput: ElementGetter<HTMLInputElement>,
        private readonly getMenu: ElementGetter<ListSelect>,
    ) {
        host.addController(this);
    }

    /**
     * Reconcile the popover's actual open state with the host's `open` state.
     * Called after the host updates so the menu has rendered.
     */
    public hostUpdated() {
        const menu = this.getMenu();

        if (!menu) {
            this.#stopTracking();
            return;
        }

        const popoverOpen = menu.matches(":popover-open");

        if (this.host.open && !this.host.readOnly && !popoverOpen) {
            menu.showPopover();
            // Start tracking synchronously (not via the async `toggle` event) so the menu
            // is placed in the same frame it becomes visible — no flash at the UA default
            // position.
            this.#startTracking();
        } else if ((!this.host.open || this.host.readOnly) && popoverOpen) {
            menu.hidePopover();
        }
    }

    public hostDisconnected() {
        this.#stopTracking();
    }

    public readonly handleInputClick = (event: Event) => {
        if (this.host.readOnly) return;

        const configuredDelay = getComputedStyle(this.host).getPropertyValue(
            "--ak-search-select--RefocusDelay",
        );
        const refocusDelay = parseInt(configuredDelay, 10) || DEFAULT_REFOCUS_DELAY;
        const dismissedByThisClick = event.timeStamp - this.#lastLightDismiss < refocusDelay;

        this.host.open = dismissedByThisClick ? false : !this.host.open;
        // preventScroll: an auto-scroll here would shift the anchor in the same beat the
        // menu is being placed against it.
        this.getInput()?.focus({ preventScroll: true });
    };

    public readonly handleMenuToggle = (event: ToggleEvent) => {
        // Opening is handled synchronously in hostUpdated; here we only react to closes
        // (including browser-driven light dismiss / Esc).
        if (event.newState === "open") return;

        this.#stopTracking();

        // Record when the browser closes the popover so a click on the input that
        // caused the dismiss doesn't immediately reopen it.
        this.#lastLightDismiss = event.timeStamp;

        if (this.host.open) {
            this.host.open = false;
        }
    };

    /**
     * Forward wheel scrolling to the input's nearest scrollable ancestor once the
     * menu itself can't scroll any further in that direction. The menu is a
     * top-layer, fixed-position popover, so the browser chains its overscroll to the
     * viewport rather than to the (e.g. modal dialog) container behind it — meaning
     * scrolling over the menu would otherwise appear stuck.
     */
    public readonly handleMenuWheel = (event: WheelEvent) => {
        const menu = this.getMenu();
        if (!menu) return;

        const goingDown = event.deltaY > 0;
        const menuCanScroll = goingDown
            ? Math.ceil(menu.scrollTop + menu.clientHeight) < menu.scrollHeight
            : menu.scrollTop > 0;

        if (menuCanScroll) return;

        const scroller = findScrollableAncestor(this.host);
        if (!scroller) return;

        const deltaY = (() => {
            switch (event.deltaMode) {
                case WheelEvent.DOM_DELTA_LINE: {
                    const lineHeight = parseFloat(getComputedStyle(scroller).lineHeight);
                    return event.deltaY * (Number.isFinite(lineHeight) ? lineHeight : 16);
                }
                case WheelEvent.DOM_DELTA_PAGE:
                    return event.deltaY * scroller.clientHeight;
                default:
                    return event.deltaY;
            }
        })();

        scroller.scrollTop += deltaY;
        event.preventDefault();
    };

    #startTracking() {
        const input = this.getInput();
        const menu = this.getMenu();
        if (!input || !menu) return;

        // Close the menu when its anchor input is no longer visible — scrolled out
        // of the viewport, clipped away by a scroll container, or hidden.
        this.#anchorObserver?.disconnect();
        this.#anchorObserver = new IntersectionObserver(
            (entries) => {
                if (entries.some((entry) => !entry.isIntersecting)) {
                    this.host.open = false;
                }
            },
            { threshold: 0 },
        );
        this.#anchorObserver.observe(input);

        // Position the menu imperatively and keep it in sync. We can't rely on a global
        // scroll listener: `scroll` events are `composed: false`, so scrolling inside a
        // shadow-rendered container (e.g. a modal dialog body) never reaches `window`.
        // Instead we re-place the menu each animation frame while open, which also covers
        // nested scrollers, layout shifts, resizes, and options arriving late.
        let lastGeometry = "";
        const reflow = () => {
            const rect = this.getInput()?.getBoundingClientRect();

            if (rect) {
                const geometry = `${rect.left},${rect.top},${rect.bottom},${rect.width},${window.innerHeight},${menu.scrollHeight}`;

                if (geometry !== lastGeometry) {
                    lastGeometry = geometry;
                    this.#positionMenu();
                }
            }

            this.#reflowFrame = requestAnimationFrame(reflow);
        };

        this.#positionMenu();
        this.#reflowFrame = requestAnimationFrame(reflow);
    }

    #stopTracking() {
        this.#anchorObserver?.disconnect();
        this.#anchorObserver = undefined;

        if (this.#reflowFrame !== undefined) {
            cancelAnimationFrame(this.#reflowFrame);
            this.#reflowFrame = undefined;
        }
    }

    #positionMenu() {
        const input = this.getInput();
        const menu = this.getMenu();
        if (!input || !menu) return;

        placeAnchoredPopover(input, menu, { matchAnchorWidth: true });
    }
}

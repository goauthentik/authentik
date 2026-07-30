import "#elements/ak-list-select/ak-list-select";

import { findFlatOptions, findOptionsSubset, groupOptions, optionsToFlat } from "./utils.js";

import { ListSelect } from "#elements/ak-list-select/ak-list-select";
import { AKElement } from "#elements/Base";
<<<<<<< HEAD
import { bound } from "#elements/decorators/bound";
=======
import { AnchorPositionSupported, AnchorSizeSupported } from "#elements/dialogs/positioning";
import Styles from "#elements/forms/SearchSelect/ak-search-select-view.css";
>>>>>>> a690485a1 (website/docs: release 2026.8: fix missing headers (#24522))
import type { GroupedOptions, SelectOption, SelectOptions } from "#elements/types";
import { randomId } from "#elements/utils/randomId";

import { msg } from "@lit/localize";
<<<<<<< HEAD
import { html, nothing, PropertyValues } from "lit";
=======
import { CSSResult, html, PropertyValues } from "lit";
>>>>>>> a690485a1 (website/docs: release 2026.8: fix missing headers (#24522))
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { createRef, ref, Ref } from "lit/directives/ref.js";

import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFSelect from "@patternfly/patternfly/components/Select/select.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

const DEFAULT_REFOCUS_DELAY = 250;

/**
 * Whether this browser can position *and* size the menu against its anchor purely
 * in CSS. When true the menu uses native anchor positioning (which tracks scrolling
 * for free); otherwise it is placed imperatively. `AnchorSizeSupported` already
 * excludes Firefox, whose anchor positioning mis-renders inside a `<dialog>` despite
 * reporting support — see {@link "#elements/dialogs/positioning"}.
 */
const CSSAnchorPositioningSupported = AnchorPositionSupported && AnchorSizeSupported;

export interface ISearchSelectView {
    options: SelectOptions;
    value?: string;
    open: boolean;
    blankable: boolean;
    caseSensitive: boolean;
    name?: string;
    placeholder: string;
    managed: boolean;
    emptyOption: string;
}

/**
 * @class SearchSelectView
 * @element ak-search-select-view
 *
 * Main component of ak-search-select, renders the <input> object and controls interaction with the
 * portaled menu list.
 *
 * - @prop options! (GroupedOptions): The options passed to the component
 * - @attr value? (string): The current value. Reflected.
 * - @attr open (boolean): if the menu dropdown is visible
 * - @attr blankable (boolean): if true, the component is blankable and can return `undefined`
 * - @attr managed (boolean): if true, the options and search are managed by a higher-level
     component.
 * - @attr caseSensitive (boolean): if `managed`, local searches will be case sensitive. False by
     default.
 * - @attr name? (string): The name of the component, for forms
 * - @attr placeholder (string): What to show when the input is empty
 * - @attr emptyOption (string): What to show in the menu to indicate "leave this undefined". Only
 *   shown if `blankable`
 *
 * - @fires change - When a value from the list has been positively chosen, either as a consequence of
 *   the user typing or when selecting from the list.
 *
 * - @part ak-search-select: The main Patternfly div
 * - @part ak-search-select-toggle: The Patternfly inner div
 * - @part ak-search-select-wrapper: Yet another Patternfly inner div
 * - @part ak-search-select-toggle-typeahead: The `<input>` component itself
 *
 * Note that this is more on the HTML / Web Component side of the operational line: the keys which
 * represent the values we pass back to clients are always strings here. This component is strictly
 * for *rendering* and *interacting* with the items as the user sees them.  If the host client is
 * not using strings for the values it ultimately keeps inside, it must map them forward to the
 * string-based keys we use here (along with the label and description), and map them *back* to
 * the object that key references when extracting the value for use.
 *
 */
@customElement("ak-search-select-view")
export class SearchSelectView extends AKElement implements ISearchSelectView {
<<<<<<< HEAD
    static styles = [PFBase, PFForm, PFFormControl, PFSelect];
=======
    static styles: CSSResult[] = [
        // ---
        PFForm,
        PFFormControl,
        PFSelect,
        Styles,
    ];

    //#region Properties
>>>>>>> a690485a1 (website/docs: release 2026.8: fix missing headers (#24522))

    /**
     * The options collection. The simplest variant is just [key, label, optional<description>]. See
     * the `./types.ts` file for variants and how to use them.
     *
     * @prop
     */
    @property({ type: Array, attribute: false })
    set options(options: SelectOptions) {
        this._options = groupOptions(options);
        this.flatOptions = optionsToFlat(this._options);
    }

    get options() {
        return this._options;
    }

    _options!: GroupedOptions;

    /**
     * The current value.  Must be one of the keys in the options group above.
     *
     * @prop
     */
    @property({ type: String, reflect: true })
    value?: string;

    /**
     * Whether or not the dropdown is open
     *
     * @attr
     */
    @property({ type: Boolean, reflect: true })
    open = false;

    /**
     * If set to true, this object MAY return undefined in no value is passed in and none is set
     * during interaction.
     *
     * @attr
     */
    @property({ type: Boolean })
    blankable = false;

    /**
     * If not managed, make the matcher case-sensitive during interaction.  If managed,
     * the manager must handle this.
     *
     * @attr
     */
    @property({ type: Boolean, attribute: "case-sensitive" })
    caseSensitive = false;

    /**
     * The name of the input, for forms
     *
     * @attr
     */
    @property({ type: String })
    name?: string;

    /**
     * The textual placeholder for the search's <input> object, if currently empty. Used as the
     * native <input> object's `placeholder` field.
     *
     * @attr
     */
    @property({ type: String })
    placeholder: string = msg("Select an object.");

    /**
     * If true, the component only sends an input message up to a parent component. If false, the
     * list of options sent downstream will be filtered by the contents of the `<input>` field
     * locally.
     *
     *@attr
     */
    @property({ type: Boolean })
    managed = false;

    /**
     * A textual string representing "The user has affirmed they want to leave the selection blank."
     * Only used if `blankable` above is true.
     *
     * @attr
     */
    @property()
    emptyOption = "---------";

    // Handle the behavior of the drop-down when the :host scrolls off the page.
    scrollHandler?: () => void;

    // observer: IntersectionObserver;

    @state()
    displayValue = "";

<<<<<<< HEAD
    // Tracks when the inputRef is populated, so we can safely reschedule the
    // render of the dropdown with respect to it.
    @state()
    inputRefIsAvailable = false;

=======
>>>>>>> a690485a1 (website/docs: release 2026.8: fix missing headers (#24522))
    /**
     * Permanent identity with the portal so focus events can be checked.
     */
    menuRef: Ref<ListSelect> = createRef();

    /**
     * Permanent identify for the input object, so the floating portal can find where to anchor
     * itself.
     */
    inputRef: Ref<HTMLInputElement> = createRef();

    /**
     *  Maps a value from the portal to labels to be put into the <input> field>
     */
<<<<<<< HEAD
    flatOptions: [string, SelectOption][] = [];
=======
    #flatOptions: [label: string, option: SelectOption][] = [];

    //#endregion

    //#region Lifecycle

    public override updated() {
        this.#syncMenuVisibility();
        this.setAttribute("data-ouia-component-safe", "true");
    }

    /**
     * Reconcile the popover's actual open state with `this.open`.
     * Called from `updated()` so it runs after the menu has rendered.
     */
    #syncMenuVisibility() {
        const menu = this.#menuRef.value;
        if (!menu) return;

        const popoverOpen = menu.matches(":popover-open");

        if (this.open && !this.readOnly && !popoverOpen) {
            menu.showPopover();
            // Start tracking synchronously (not via the async `toggle` event) so the
            // fallback places the menu in the same frame it becomes visible — no flash
            // at the UA default position.
            this.#startAnchorTracking();
        } else if ((!this.open || this.readOnly) && popoverOpen) {
            menu.hidePopover();
        }
    }
>>>>>>> a690485a1 (website/docs: release 2026.8: fix missing headers (#24522))

    connectedCallback() {
        super.connectedCallback();
        this.setAttribute("data-ouia-component-type", "ak-search-select-view");
        this.setAttribute("data-ouia-component-id", this.getAttribute("id") || randomId());
        // Styling hook: opt this instance into the CSS anchor-positioning block.
        this.toggleAttribute("data-anchor-css", CSSAnchorPositioningSupported);
    }

    disconnectedCallback() {
        this.#stopAnchorTracking();
        super.disconnectedCallback();
    }

    // TODO: Reconcile value <-> display value, Reconcile option changes to value <-> displayValue

    // If the user has changed the content of the input box, they are manipulating the *Label*, not
    // the value. We'll have to retroactively decide the value and publish it to any listeners.
    settleValue() {
        // TODO
    }

<<<<<<< HEAD
    @bound
    onClick(_ev: Event) {
        this.open = !this.open;
        this.inputRef.value?.focus();
    }

    setFromMatchList(value: string | undefined) {
        if (value === undefined) {
            return;
        }
        const probableValue = this.flatOptions.find((option) => option[0] === this.value);
        if (probableValue && this.inputRef.value) {
            this.inputRef.value.value = probableValue[1][1];
=======
    //#endregion

    //#region Event Listeners

    /** Timestamp of the last browser-driven popover close (see reopen guard). */
    #lastLightDismiss = -Infinity;

    #clickListener = (event: Event) => {
        if (this.readOnly) return;

        const computedRefocusDelay = getComputedStyle(this)?.getPropertyValue(
            "--ak-search-select--RefocusDelay",
        );

        const refocusDelay = parseInt(computedRefocusDelay, 10) || DEFAULT_REFOCUS_DELAY;

        // If this same click just light-dismissed the open popover, treat it as a
        // close: leave `open` false instead of toggling it back on.
        const dismissedByThisClick = event.timeStamp - this.#lastLightDismiss < refocusDelay;

        this.open = dismissedByThisClick ? false : !this.open;
        this.#inputRef.value?.focus();
    };

    /**
     * Reflect browser-driven popover state changes (light dismiss, Esc) back
     * into `this.open`, keeping component state authoritative.
     */
    #menuToggleListener = (event: ToggleEvent) => {
        // Opening is handled synchronously in #syncMenuVisibility; here we only
        // react to closes (including browser-driven light dismiss / Esc).
        if (event.newState === "open") return;

        this.#stopAnchorTracking();

        // Record when the browser closes the popover so a click on the input
        // that *caused* the dismiss doesn't immediately reopen it.
        this.#lastLightDismiss = event.timeStamp;

        if (this.open) {
            this.open = false;
        }
    };

    /**
     * Forward wheel scrolling to the input's nearest scrollable ancestor once the
     * menu itself can't scroll any further in that direction. The menu is a
     * top-layer, fixed-position popover, so the browser chains its overscroll to the
     * viewport rather than to the (e.g. modal dialog) container behind it — meaning
     * scrolling over the menu would otherwise appear stuck.
     */
    #menuWheelListener = (event: WheelEvent) => {
        const menu = this.#menuRef.value;
        if (!menu) return;

        const goingDown = event.deltaY > 0;
        const menuCanScroll = goingDown
            ? Math.ceil(menu.scrollTop + menu.clientHeight) < menu.scrollHeight
            : menu.scrollTop > 0;

        if (menuCanScroll) return;

        const scroller = this.#findScrollableAncestor();
        if (!scroller) return;

        const deltaY = (() => {
            switch (event.deltaMode) {
                case WheelEvent.DOM_DELTA_LINE: {
                    const lh = parseFloat(getComputedStyle(scroller).lineHeight);
                    return event.deltaY * (Number.isFinite(lh) ? lh : 16);
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

    /**
     * Walk the flattened (composed) tree upward from this element — crossing shadow
     * boundaries and slots — to the nearest vertically scrollable ancestor.
     */
    #findScrollableAncestor(): HTMLElement | null {
        const composedParent = (node: Node): Node | null => {
            const slot = (node as Element).assignedSlot;
            if (slot) return slot;

            const parent = node.parentNode;
            return parent instanceof ShadowRoot ? parent.host : parent;
        };

        for (let node = composedParent(this); node; node = composedParent(node)) {
            if (!(node instanceof HTMLElement)) continue;

            const { overflowY } = getComputedStyle(node);
            const scrollable =
                overflowY === "auto" || overflowY === "scroll" || overflowY === "overlay";

            if (scrollable && node.scrollHeight > node.clientHeight) {
                return node;
            }
        }

        return null;
    }

    #anchorObserver?: IntersectionObserver;

    #startAnchorTracking() {
        const input = this.#inputRef.value;
        const menu = this.#menuRef.value;

        if (!input || !menu) return;

        // Close the menu when its anchor input is no longer visible — scrolled out
        // of the viewport, clipped away by a scroll container, or hidden. This works
        // in every browser regardless of anchor-positioning support.
        this.#anchorObserver?.disconnect();
        this.#anchorObserver = new IntersectionObserver(
            (entries) => {
                if (entries.some((entry) => !entry.isIntersecting)) {
                    this.open = false;
                }
            },
            { threshold: 0 },
        );
        this.#anchorObserver.observe(input);

        // Native CSS anchor positioning handles placement and tracks scrolling on its
        // own — nothing else to do.
        if (CSSAnchorPositioningSupported) return;

        // Otherwise position the menu imperatively and keep it in sync. We can't rely
        // on a global scroll listener: `scroll` events are `composed: false`, so
        // scrolling inside a shadow-rendered container (e.g. a modal dialog body)
        // never reaches `window`. Instead we re-place the menu each animation frame
        // while open, which also covers nested scrollers, layout shifts, and resizes.
        let lastGeometry = "";

        const reflow = () => {
            const rect = this.#inputRef.value?.getBoundingClientRect();

            if (rect) {
                const geometry = `${rect.left},${rect.top},${rect.bottom},${rect.width},${window.innerHeight}`;

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

    #reflowFrame?: number;

    #stopAnchorTracking() {
        this.#anchorObserver?.disconnect();
        this.#anchorObserver = undefined;

        if (this.#reflowFrame !== undefined) {
            cancelAnimationFrame(this.#reflowFrame);
            this.#reflowFrame = undefined;
        }
    }

    /**
     * Position the menu against the input imperatively, matching the CSS
     * anchor-positioning behavior (below by default, flip above when there's no
     * room, width matched to the input, capped height). Only used where CSS anchor
     * positioning is unavailable.
     */
    #positionMenu() {
        const input = this.#inputRef.value;
        const menu = this.#menuRef.value;

        if (!input || !menu) return;

        const rect = input.getBoundingClientRect();
        const viewportHeight = window.innerHeight;
        const maxHeight = Math.round(viewportHeight * 0.4);
        const menuHeight = Math.min(menu.offsetHeight || maxHeight, maxHeight);

        const spaceBelow = viewportHeight - rect.bottom;
        const flipUp = spaceBelow < menuHeight && rect.top > spaceBelow;

        menu.style.position = "fixed";
        menu.style.left = `${Math.round(rect.left)}px`;
        menu.style.width = `${Math.round(rect.width)}px`;
        menu.style.maxHeight = `${maxHeight}px`;

        if (flipUp) {
            menu.style.top = "auto";
            menu.style.bottom = `${Math.round(viewportHeight - rect.top)}px`;
        } else {
            menu.style.bottom = "auto";
            menu.style.top = `${Math.round(rect.bottom)}px`;
        }
    }

    setFromMatchList(value?: string) {
        if (!value) return;

        const probableValue = this.#flatOptions.find(([label]) => label === this.value);

        if (probableValue && this.#inputRef.value) {
            this.#inputRef.value.value = probableValue[1][1];
>>>>>>> a690485a1 (website/docs: release 2026.8: fix missing headers (#24522))
        }
    }

    @bound
    onKeydown(event: KeyboardEvent) {
        if (event.code === "Escape") {
            event.stopPropagation();
            this.open = false;
        }
        if (event.code === "ArrowDown" || event.code === "ArrowUp") {
            this.open = true;
        }
        if (event.code === "Tab" && this.open) {
            event.preventDefault();
            this.setFromMatchList(this.value);
            this.menuRef.value?.currentElement?.focus();
        }
    }

    @bound
    onListBlur(event: FocusEvent) {
        // If we lost focus but the menu got it, don't do anything;
        const relatedTarget = event.relatedTarget as HTMLElement | undefined;
        if (
            relatedTarget &&
            (this.contains(relatedTarget) ||
                this.renderRoot.contains(relatedTarget) ||
                this.menuRef.value?.contains(relatedTarget) ||
                this.menuRef.value?.renderRoot.contains(relatedTarget))
        ) {
            return;
        }
        this.open = false;
        if (this.value === undefined) {
            if (this.inputRef.value) {
                this.inputRef.value.value = "";
            }
            this.setValue(undefined);
        }
    }

    setValue(newValue: string | undefined) {
        this.value = newValue;
        this.dispatchEvent(new Event("change", { bubbles: true, composed: true })); // prettier-ignore
    }

    findValueForInput() {
        const value = this.inputRef.value?.value;
        if (value === undefined || value.trim() === "") {
            this.setValue(undefined);
            return;
        }

        const matchesFound = findFlatOptions(this.flatOptions, value);
        if (matchesFound.length > 0) {
            const newValue = matchesFound[0][0];
            if (newValue === value) {
                return;
            }
            this.setValue(newValue);
        } else {
            this.setValue(undefined);
        }
    }

    @bound
    onInput(_ev: InputEvent) {
        if (!this.managed) {
            this.findValueForInput();
            this.requestUpdate();
        }
        this.open = true;
    }

    @bound
    onListKeydown(event: KeyboardEvent) {
        if (event.key === "Escape") {
            this.open = false;
            this.inputRef.value?.focus();
        }
        if (event.key === "Tab" && event.shiftKey) {
            event.preventDefault();
            this.inputRef.value?.focus();
        }
    }

    @bound
    onListChange(event: InputEvent) {
        if (!event.target) {
            return;
        }
        const value = (event.target as HTMLInputElement).value;
        if (value !== undefined) {
            const newDisplayValue = this.findDisplayForValue(value);
            if (this.inputRef.value) {
                this.inputRef.value.value = newDisplayValue ?? "";
            }
        } else if (this.inputRef.value) {
            this.inputRef.value.value = "";
        }
        this.open = false;
        this.setValue(value);
    }

    findDisplayForValue(value: string) {
        const newDisplayValue = this.flatOptions.find((option) => option[0] === value);
        return newDisplayValue ? newDisplayValue[1][1] : undefined;
    }

    public override performUpdate() {
        this.removeAttribute("data-ouia-component-safe");
        super.performUpdate();
    }

    public override willUpdate(changed: PropertyValues<this>) {
        if (changed.has("value") && this.value) {
            const newDisplayValue = this.findDisplayForValue(this.value);
            if (newDisplayValue) {
                this.displayValue = newDisplayValue;
            }
        }
    }

    get rawValue() {
        return this.inputRef.value?.value ?? "";
    }

    get managedOptions() {
        return this.managed
            ? this._options
            : findOptionsSubset(this._options, this.rawValue, this.caseSensitive);
    }

    public override render() {
<<<<<<< HEAD
        const emptyOption = this.blankable ? this.emptyOption : undefined;
        const open = this.open;
=======
        const emptyOption = this.blankable
            ? this.emptyOption || this.placeholder || msg("Select an option...")
            : null;
>>>>>>> a690485a1 (website/docs: release 2026.8: fix missing headers (#24522))

        return html`<div class="pf-c-select" part="ak-search-select">
                <div class="pf-c-select__toggle pf-m-typeahead" part="ak-search-select-toggle">
                    <div class="pf-c-select__toggle-wrapper" part="ak-search-select-wrapper">
                        <input
                            part="ak-search-select-toggle-typeahead"
                            autocomplete="off"
                            class="pf-c-form-control pf-c-select__toggle-typeahead"
                            type="text"
                            ${ref(this.inputRef)}
                            placeholder=${this.placeholder}
                            spellcheck="false"
                            @input=${this.onInput}
                            @click=${this.onClick}
                            @blur=${this.onListBlur}
                            @keydown=${this.onKeydown}
                            value=${this.displayValue}
                        />
                    </div>
                </div>
            </div>
<<<<<<< HEAD
            ${this.inputRefIsAvailable
                ? html`
                      <ak-portal
                          name=${ifDefined(this.name)}
                          .anchor=${this.inputRef.value}
                          ?open=${open}
                      >
                          <ak-list-select
                              id="menu-${this.getAttribute("data-ouia-component-id")}"
                              ${ref(this.menuRef)}
                              .options=${this.managedOptions}
                              value=${ifDefined(this.value)}
                              @change=${this.onListChange}
                              @blur=${this.onListBlur}
                              emptyOption=${ifDefined(emptyOption)}
                              @keydown=${this.onListKeydown}
                          ></ak-list-select>
                      </ak-portal>
                  `
                : nothing}`;
=======
            <ak-list-select
                popover="auto"
                id="menu-${this.getAttribute("data-ouia-component-id")}"
                ${ref(this.#menuRef)}
                .options=${this.managedOptions}
                value=${ifDefined(this.value)}
                @change=${this.#changeListener}
                @blur=${this.#blurListener}
                @toggle=${this.#menuToggleListener}
                @wheel=${this.#menuWheelListener}
                emptyOption=${ifPresent(emptyOption)}
                actionLabel=${ifPresent(this.actionLabel)}
                @ak-select-action=${this.#actionListener}
                @keydown=${this.#listKeydownListener}
                @keyup=${this.#listKeyupListener}
            ></ak-list-select>`;
>>>>>>> a690485a1 (website/docs: release 2026.8: fix missing headers (#24522))
    }

    public override updated() {
        this.setAttribute("data-ouia-component-safe", "true");
    }

    public override firstUpdated() {
        // Route around Lit's scheduling algorithm complaining about re-renders
        window.setTimeout(() => {
            this.inputRefIsAvailable = Boolean(this.inputRef?.value);
        }, 0);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-search-select-view": SearchSelectView;
    }
}

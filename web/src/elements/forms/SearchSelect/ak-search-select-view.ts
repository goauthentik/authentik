import { AKElement } from "@goauthentik/elements/Base";
import { bound } from "@goauthentik/elements/decorators/bound.js";
import "@goauthentik/elements/forms/SearchSelect/ak-search-select-menu-position.js";
import type { SearchSelectMenuPosition } from "@goauthentik/elements/forms/SearchSelect/ak-search-select-menu-position.js";
import { randomId } from "@goauthentik/elements/utils/randomId.js";

import { msg } from "@lit/localize";
import { PropertyValues, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { Ref, createRef, ref } from "lit/directives/ref.js";

import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFSelect from "@patternfly/patternfly/components/Select/select.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import {
    SearchSelectInputEvent,
    SearchSelectMenuLostFocusEvent,
    SearchSelectRequestCloseEvent,
    SearchSelectSelectItemEvent,
} from "./SearchSelectEvents.js";
import type { SearchOptions, SearchTuple } from "./types.js";

/**
 * @class SearchSelectView
 * @element ak-search-select-view
 *
 * Main component of ak-search-select, renders the <input> object and controls interaction with the
 * portaled menu list.
 *
 * @fires ak-search-select-input - When the user selects an item from the list. A derivative Event
 * with the `value` as its payload.
 *
 * Note that this is more on the HTML / Web Component side of the operational line: the keys which
 * represent the values we pass back to clients are always strings here. This component is strictly
 * for *rendering* and *interacting* with the items as the user sees them.  If the host client is
 * not using strings for the values it ultimately keeps inside, it must map them forward to the
 * string-based keys we use here (along with the label and description), and map them *back* to
 * the object that key references when extracting the value for use.
 *
 */

enum InputState {
    idle = 0, // Closed and nothing has focus
    closed = 1, // The input has focus, the dropdown is closed
    open = 2, // The dropdown is open, focus is context-dependent
    justclosed = 3, // Transitional state.
}

@customElement("ak-search-select-view")
export class SearchSelectView extends AKElement {
    /**
     * The options collection. The simplest variant is just [key, label, optional<description>]. See
     * the `./types.ts` file for variants and how to use them.
     *
     * @prop
     */
    @property({ type: Array, attribute: false })
    options: SearchOptions = [];

    /**
     * The current value.  Must be one of the keys in the options group above.
     *
     * @prop
     */
    @property()
    value?: string;

    /**
     * If set to true, this object MAY return undefined in no value is passed in and none is set
     * during interaction.
     *
     * @attr
     */
    @property({ type: Boolean })
    blankable = false;

    /**
     * The name of the input, for forms
     *
     * @attr
     */
    @property()
    name?: string;

    /**
     * The textual placeholder for the search's <input> object, if currently empty. Used as the
     * native <input> object's `placeholder` field.
     *
     * @attr
     */
    @property()
    placeholder: string = msg("Select an object.");

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
    /**
     * Permanent identify for the input object, so the floating portal can find where to anchor
     * itself.
     */
    inputRef: Ref<HTMLInputElement> = createRef();

    /**
     * Permanent identity with the portal so focus events can be checked.
     */
    menuRef: Ref<SearchSelectMenuPosition> = createRef();

    /**
     *  Maps a value from the portal to labels to be put into the <input> field>
     */
    optionsMap: Map<string, string> = new Map();

    /**
     * Controls when focus should be re-acquired
     */
    @state()
    inputState: InputState = InputState.idle;

    static get styles() {
        return [PFBase, PFForm, PFFormControl, PFSelect];
    }

    constructor() {
        super();
        /* These can't be attached with the `@` syntax because they're not passed through to the
         * menu; the positioner is in the way, and it deliberately renders objects *outside* of the
         * event path from `document` to this object. That's why we pass the positioner (and its
         * target) the `this` (host) object; so they can send messages to this object despite being
         * outside the event's bubble path.
         */
        this.addEventListener(SearchSelectMenuLostFocusEvent.eventName, this.onMenuLostFocus);
        this.addEventListener(SearchSelectRequestCloseEvent.eventName, this.onMenuRequestClose);
        this.addEventListener(SearchSelectSelectItemEvent.eventName, this.onSelectItemEvent);
    }

    connectedCallback() {
        super.connectedCallback();
        console.log("Was this ever called?");
        this.setAttribute("data-ouia-component-type", "ak-search-select-view");
        this.setAttribute("data-ouia-component-id", this.getAttribute("id") || randomId());
    }

    disconnectedCallback(): void {
        super.disconnectedCallback();
    }

    // TODO: Reconcile value <-> display value, Reconcile option changes to value <-> displayValue

    // If the user has changed the content of the input box, they are manipulating the *Label*, not
    // the value. We'll have to retroactively decide the value and publish it to any listeners.
    settleValue() {
        // TODO
    }

    checkBlankableValue(ev: Event) {
        if (
            this.blankable &&
            ev.target &&
            this.value === this.emptyOption &&
            ev.target instanceof HTMLInputElement
        ) {
            ev.target.value = "";
        }
    }

    @bound
    onMenuLostFocus(ev: SearchSelectMenuLostFocusEvent) {
        console.log("Menu lost focus.");
        ev.stopImmediatePropagation();
        // If neither the input or the menu has the focus after the previous event phase is settled,
        // then the menu must be closed.
        window.setTimeout(() => {
            if (this.inputRef.value?.matches(":focus")) {
                console.log("Input Had Focus.");
                return;
            }
            if (!this.menuRef.value?.hasFocus) {
                this.inputState = InputState.idle;
                this.settleValue();
            }
        }, 0);
    }

    @bound
    onMenuRequestClose(ev: SearchSelectRequestCloseEvent) {
        // Simple enough: the user hit `Escape` while the menu had the focus.
        ev.stopImmediatePropagation();
    }

    @bound
    onSelectItemEvent(ev: SearchSelectSelectItemEvent) {
        ev.stopImmediatePropagation();
        this.value = ev.value;
        this.displayValue = this.value ? (this.optionsMap.get(this.value) ?? this.value ?? "") : "";
        this.dispatchEvent(new SearchSelectInputEvent(this.value));
    }

    @bound
    onInput(_ev: InputEvent) {
        // We don't stop this propagation. If parent elements want to handle it, they can.
        // Any change may trigger a request that changes the option set upstream.  That
        // requires a re-show of the menu.
        this.dispatchEvent(new SearchSelectInputEvent(this.inputRef?.value?.value ?? ""));
        this.settleValue();
    }

    @bound
    onClick(ev: Event) {
        this.inputState =
            this.inputState === InputState.justclosed || this.options.length == 0
                ? InputState.closed
                : InputState.open;
        this.checkBlankableValue(ev);
    }

    @bound
    onKeydown(event: KeyboardEvent) {
        if (event.key === "Escape") {
            event.stopPropagation();
        }
    }

    @bound
    onFocusOut(event: FocusEvent) {
        console.log("Input lost focus.");
        event.stopPropagation();
        // If neither the input or the menu has the focus after the previous event phase is settled,
        // then the menu must be closed.
        window.setTimeout(() => {
            if (!this.menuRef.value?.hasFocus && !this.inputRef.value?.matches(":focus")) {
                this.inputState = InputState.idle;
            }
        }, 0);
    }

    willUpdate(changed: PropertyValues<this>) {
        this.removeAttribute("data-ouia-component-safe");
        if (changed.has("options")) {
            this.optionsMap = optionsToOptionsMap(this.options);
        }
        if (changed.has("value")) {
            this.displayValue = this.value
                ? (this.optionsMap.get(this.value ?? "") ?? this.value ?? "")
                : "";
        }
    }

    updated() {
        if (!(this.inputRef?.value && this.inputRef?.value?.value === this.displayValue)) {
            this.inputRef.value && (this.inputRef.value.value = this.displayValue);
        }
        this.setAttribute("data-ouia-component-safe", true);
    }

    render() {
        return html`<div class="pf-c-select">
                <div class="pf-c-select__toggle pf-m-typeahead">
                    <div class="pf-c-select__toggle-wrapper">
                        <input
                            autocomplete="off"
                            class="pf-c-form-control pf-c-select__toggle-typeahead"
                            type="text"
                            ${ref(this.inputRef)}
                            placeholder=${this.placeholder}
                            spellcheck="false"
                            @input=${this.onInput}
                            @click=${this.onClick}
                            @focus=${this.onClick}
                            @keydown=${this.onKeydown}
                            value=${this.displayValue}
                        />
                    </div>
                </div>
            </div>
            <ak-search-select-menu-position
                name=${ifDefined(this.name)}
                .options=${this.options}
                value=${ifDefined(this.value)}
                .host=${this}
                .anchor=${this.inputRef.value}
                .emptyOption=${(this.blankable && this.emptyOption) || undefined}
                ${ref(this.menuRef)}
                ?open=${this.inputState === InputState.open}
            ></ak-search-select-menu-position> `;
    }
}

type Pair = [string, string];
const justThePair = ([key, label]: SearchTuple): Pair => [key, label];

function optionsToOptionsMap(options: SearchOptions): Map<string, string> {
    const pairs: Pair[] = Array.isArray(options)
        ? options.map(justThePair)
        : options.grouped
          ? options.options.reduce(
                (acc: Pair[], { options }): Pair[] => [...acc, ...options.map(justThePair)],
                [] as Pair[],
            )
          : options.options.map(justThePair);
    return new Map(pairs);
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-search-select-view": SearchSelectView;
    }
}

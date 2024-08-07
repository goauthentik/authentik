import { AKElement } from "@goauthentik/elements/Base";
import { bound } from "@goauthentik/elements/decorators/bound.js";
import "@goauthentik/elements/forms/SearchSelect/ak-search-select-menu-position.js";
import type { SearchSelectMenuPosition } from "@goauthentik/elements/forms/SearchSelect/ak-search-select-menu-position.js";

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
    SearchSelectCloseEvent,
    SearchSelectInputEvent,
    SearchSelectSelectEvent,
    SearchSelectSelectMenuEvent,
} from "./SearchSelectEvents.js";
import type { SearchOptions } from "./types.js";
import { optionsToOptionsMap } from "./utils.js";

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
     * Whether or not the portal is open
     *
     * @attr
     */
    @property({ type: Boolean, reflect: true })
    open = false;

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
    observer: IntersectionObserver;

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

    static get styles() {
        return [PFBase, PFForm, PFFormControl, PFSelect];
    }

    constructor() {
        super();
        this.observer = new IntersectionObserver(() => {
            this.open = false;
        });
        this.observer.observe(this);

        /* These can't be attached with the `@` syntax because they're not passed through to the
         * menu; the positioner is in the way, and it deliberately renders objects *outside* of the
         * path from `document` to this object. That's why we pass the positioner (and its target)
         * the `this` (host) object; so they can send messages to this object despite being outside
         * the event's bubble path.
         */
        this.addEventListener("ak-search-select-select-menu", this.onSelect);
        this.addEventListener("ak-search-select-close", this.onClose);
    }

    disconnectedCallback(): void {
        this.observer.disconnect();
        super.disconnectedCallback();
    }

    onOpenEvent(event: Event) {
        this.open = true;
        if (
            this.blankable &&
            this.value === this.emptyOption &&
            event.target &&
            event.target instanceof HTMLInputElement
        ) {
            event.target.value = "";
        }
    }

    @bound
    onSelect(event: SearchSelectSelectMenuEvent) {
        this.open = false;
        this.value = event.value;
        this.displayValue = this.value ? (this.optionsMap.get(this.value) ?? this.value ?? "") : "";
        this.dispatchEvent(new SearchSelectSelectEvent(this.value));
    }

    @bound
    onClose(event: SearchSelectCloseEvent) {
        event.stopPropagation();
        this.inputRef.value?.focus();
        this.open = false;
    }

    @bound
    onFocus(event: FocusEvent) {
        this.onOpenEvent(event);
    }

    @bound
    onClick(event: Event) {
        this.onOpenEvent(event);
    }

    @bound
    onInput(_event: InputEvent) {
        this.value = this.inputRef?.value?.value ?? "";
        this.displayValue = this.value ? (this.optionsMap.get(this.value) ?? this.value ?? "") : "";
        this.dispatchEvent(new SearchSelectInputEvent(this.value));
    }

    @bound
    onKeydown(event: KeyboardEvent) {
        if (event.key === "Escape") {
            event.stopPropagation();
            this.open = false;
        }
    }

    @bound
    onFocusOut(event: FocusEvent) {
        event.stopPropagation();
        window.setTimeout(() => {
            if (!this.menuRef.value?.hasFocus()) {
                this.open = false;
            }
        }, 0);
    }

    willUpdate(changed: PropertyValues<this>) {
        if (changed.has("options")) {
            this.optionsMap = optionsToOptionsMap(this.options);
        }
        if (changed.has("value")) {
            this.displayValue = this.value
                ? (this.optionsMap.get(this.value) ?? this.value ?? "")
                : "";
        }
    }

    updated() {
        if (this.inputRef?.value && this.inputRef?.value?.value !== this.displayValue) {
            this.inputRef.value.value = this.displayValue;
        }
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
                            @focus=${this.onFocus}
                            @click=${this.onClick}
                            @keydown=${this.onKeydown}
                            @focusout=${this.onFocusOut}
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
                ?open=${this.open}
            ></ak-search-select-menu-position> `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-search-select-view": SearchSelectView;
    }
}

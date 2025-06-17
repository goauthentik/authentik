import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/ak-list-select/ak-list-select.js";
import { ListSelect } from "@goauthentik/elements/ak-list-select/ak-list-select.js";
import { bound } from "@goauthentik/elements/decorators/bound.js";
import "@goauthentik/elements/forms/SearchSelect/ak-portal.js";
import type { GroupedOptions, SelectOption, SelectOptions } from "@goauthentik/elements/types.js";
import { randomId } from "@goauthentik/elements/utils/randomId.js";

import { msg } from "@lit/localize";
import { CSSResult, PropertyValues, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { Ref, createRef, ref } from "lit/directives/ref.js";

import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFSelect from "@patternfly/patternfly/components/Select/select.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { findFlatOptions, findOptionsSubset, groupOptions, optionsToFlat } from "./utils.js";

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
    static styles: CSSResult[] = [PFBase, PFForm, PFFormControl, PFSelect];

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
     * The name of the input, for forms.
     *
     * @attr
     */
    @property({ type: String })
    name?: string;

    /**
     * The label of the input, for forms.
     *
     * @attr
     */
    @property({ type: String })
    public label?: string;

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

    // Tracks when the inputRef is populated, so we can safely reschedule the
    // render of the dropdown with respect to it.
    @state()
    inputRefIsAvailable = false;

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
    flatOptions: [string, SelectOption][] = [];

    connectedCallback() {
        super.connectedCallback();
        this.setAttribute("data-ouia-component-type", "ak-search-select-view");
        this.setAttribute("data-ouia-component-id", this.getAttribute("id") || randomId());
    }

    // TODO: Reconcile value <-> display value, Reconcile option changes to value <-> displayValue

    // If the user has changed the content of the input box, they are manipulating the *Label*, not
    // the value. We'll have to retroactively decide the value and publish it to any listeners.
    settleValue() {
        // TODO
    }

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
        const emptyOption = this.blankable ? this.emptyOption : undefined;
        const open = this.open;

        return html`<div class="pf-c-select" part="ak-search-select">
                <div class="pf-c-select__toggle pf-m-typeahead" part="ak-search-select-toggle">
                    <div class="pf-c-select__toggle-wrapper" part="ak-search-select-wrapper">
                        <input
                            name=${ifDefined(this.name)}
                            placeholder=${this.placeholder}
                            aria-label=${ifDefined(this.label)}
                            part="ak-search-select-toggle-typeahead"
                            autocomplete="off"
                            class="pf-c-form-control pf-c-select__toggle-typeahead"
                            type="text"
                            ${ref(this.inputRef)}
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

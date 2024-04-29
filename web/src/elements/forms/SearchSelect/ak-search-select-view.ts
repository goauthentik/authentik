import { AKElement } from "@goauthentik/elements/Base";
import { bound } from "@goauthentik/elements/decorators/bound.js";
import "@goauthentik/elements/forms/SearchSelect/ak-search-select-menu-position.js";
import type { SearchSelectMenuPosition } from "@goauthentik/elements/forms/SearchSelect/ak-search-select-menu-position.js";

import { msg } from "@lit/localize";
import { PropertyValues, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { Ref, createRef, ref } from "lit/directives/ref.js";

import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFSelect from "@patternfly/patternfly/components/Select/select.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { SearchSelectClickEvent, SearchSelectCloseEvent } from "./SearchSelectMenuEvents.js";
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
     * If set to true, this object MAY return undefined in no value is passed in and none is set during interaction.
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
        this.addEventListener("ak-search-select-click", this.onInput);
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

    onCloseEvent(event: Event) {
        event.stopPropagation();
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
    onInput(event: SearchSelectClickEvent) {
        this.onCloseEvent(event);
        this.value = event.value;
        this.dispatchEvent(new SearchSelectInputEvent(event.value));
    }

    @bound
    onClose(event: SearchSelectCloseEvent) {
        this.onCloseEvent(event);
    }

    @bound
    onKeydown(event: KeyboardEvent) {
        if (event.key === "Escape") {
            this.onCloseEvent(event);
        }
    }

    @bound
    onFocusOut(event: FocusEvent) {
        event.stopPropagation();
        window.setTimeout(() => {
            if (!this.menuRef.value?.hasFocus()) {
                this.onCloseEvent(event);
            }
        }, 80);
    }

    willUpdate(changed: PropertyValues<this>) {
        if (changed.has("options")) {
            this.optionsMap = optionsToOptionsMap(this.options);
        }
    }

    render(): TemplateResult {
        const displayValue = this.value
            ? this.optionsMap.get(this.value) ?? this.emptyOption ?? ""
            : this.emptyOption ?? "";
        return html`<div class="pf-c-select">
                <div class="pf-c-select__toggle pf-m-typeahead">
                    <div class="pf-c-select__toggle-wrapper">
                        <input
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
                            value=${displayValue ?? ""}
                        />
                    </div>
                </div>
            </div>
            <ak-search-select-menu-position
                name=${ifDefined(this.name)}
                .options=${this.options}
                .value=${this.value}
                .host=${this}
                .anchor=${this.inputRef.value}
                .emptyOption=${(this.blankable && this.emptyOption) || undefined}
                ${ref(this.menuRef)}
                ?hidden=${!this.open}
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

export class SearchSelectInputEvent extends Event {
    value: string | undefined;
    constructor(value: string | undefined) {
        super("ak-search-select-input", { composed: true, bubbles: true });
        this.value = value;
    }
}

declare global {
    interface GlobalEventHandlersEventMap {
        "ak-search-select-input": SearchSelectInputEvent;
    }

    interface HTMLElementTagNameMap {
        "ak-search-select-view": SearchSelectView;
    }
}

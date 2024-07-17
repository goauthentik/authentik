import { AKElement } from "@goauthentik/elements/Base.js";
import { bound } from "@goauthentik/elements/decorators/bound.js";

import { PropertyValues, css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";
import PFSelect from "@patternfly/patternfly/components/Select/select.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { AkKeyboardController } from "./SearchKeyboardController.js";
import {
    KeyboardControllerCloseEvent,
    KeyboardControllerSelectEvent,
} from "./SearchKeyboardControllerEvents.js";
import { SearchSelectCloseEvent, SearchSelectSelectMenuEvent } from "./SearchSelectEvents.js";
import type { GroupedOptions, SearchGroup, SearchOptions, SearchTuple } from "./types.js";

/**
 * @class SearchSelectMenu
 * @element ak-search-select-menu
 *
 * The actual renderer of our components. Intended to be positioned and controlled automatically
 * from the outside.
 *
 * @fires ak-search-select-select - An element has been selected. Contains the `value` of the
 * selected item.
 *
 * @fires ak-search-select-close - The user has triggered the `close` event. Clients can do with this
 * as they wish.
 */

@customElement("ak-search-select-menu")
export class SearchSelectMenu extends AKElement {
    static get styles() {
        return [
            PFBase,
            PFDropdown,
            PFSelect,
            css`
                :host {
                    overflow: visible;
                    z-index: 9999;
                }

                :host([hidden]) {
                    display: none;
                }

                .pf-c-dropdown__menu {
                    max-height: 50vh;
                    overflow-y: auto;
                }
            `,
        ];
    }

    /**
     * The host to which all relevant events will be routed.  Useful for managing floating / tethered
     * components.
     */
    @property({ type: Object, attribute: false })
    host!: HTMLElement;

    /**
     * See the search options type, described in the `./types` file, for the relevant types.
     */
    @property({ type: Array, attribute: false })
    options: SearchOptions = [];

    @property()
    value?: string;

    @property()
    emptyOption?: string;

    @property({ type: Boolean, reflect: true })
    open = false;

    private keyboardController: AkKeyboardController;

    constructor() {
        super();
        this.keyboardController = new AkKeyboardController(this);
        this.addEventListener("ak-keyboard-controller-select", this.onKeySelect);
        this.addEventListener("ak-keyboard-controller-close", this.onKeyClose);
    }

    // Handles the "easy mode" of just passing an array of tuples.
    fixedOptions(): GroupedOptions {
        return Array.isArray(this.options)
            ? { grouped: false, options: this.options }
            : this.options;
    }

    @bound
    onClick(event: Event, value: string) {
        event.stopPropagation();
        this.host.dispatchEvent(new SearchSelectSelectMenuEvent(value));
        this.value = value;
    }

    @bound
    onEmptyClick(event: Event) {
        event.stopPropagation();
        this.host.dispatchEvent(new SearchSelectSelectMenuEvent(undefined));
        this.value = undefined;
    }

    @bound
    onKeySelect(event: KeyboardControllerSelectEvent) {
        event.stopPropagation();
        this.value = event.value;
        this.host.dispatchEvent(new SearchSelectSelectMenuEvent(this.value));
    }

    @bound
    onKeyClose(event: KeyboardControllerCloseEvent) {
        event.stopPropagation();
        this.host.dispatchEvent(new SearchSelectCloseEvent());
    }

    updated(changed: PropertyValues<this>) {
        if (changed.has("open") && this.open) {
            this.keyboardController.hostVisible();
        }
    }

    renderEmptyMenuItem() {
        return html`<li>
            <button class="pf-c-dropdown__menu-item" role="option" @click=${this.onEmptyClick}>
                ${this.emptyOption}
            </button>
        </li>`;
    }

    renderMenuItems(options: SearchTuple[]) {
        return options.map(
            ([value, label, desc]: SearchTuple) => html`
                <li>
                    <button
                        class="pf-c-dropdown__menu-item pf-m-description ak-select-item"
                        role="option"
                        value=${value}
                        @click=${(ev: Event) => {
                            this.onClick(ev, value);
                        }}
                        @keypress=${() => {
                            /* noop */
                        }}
                    >
                        <div class="pf-c-dropdown__menu-item-main">${label}</div>
                        ${desc
                            ? html`<div class="pf-c-dropdown__menu-item-description">${desc}</div>`
                            : nothing}
                    </button>
                </li>
            `,
        );
    }

    renderMenuGroups(options: SearchGroup[]) {
        return options.map(
            ({ name, options }) => html`
                <section class="pf-c-dropdown__group">
                    <h1 class="pf-c-dropdown__group-title">${name}</h1>
                    <ul>
                        ${this.renderMenuItems(options)}
                    </ul>
                </section>
            `,
        );
    }

    render() {
        const options = this.fixedOptions();
        return html`<div class="pf-c-dropdown pf-m-expanded">
            <ul class="pf-c-dropdown__menu pf-m-static" role="listbox" tabindex="0">
                ${this.emptyOption !== undefined ? this.renderEmptyMenuItem() : nothing}
                ${options.grouped
                    ? this.renderMenuGroups(options.options)
                    : this.renderMenuItems(options.options)}
            </ul>
        </div> `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-search-select-menu": SearchSelectMenu;
    }
}

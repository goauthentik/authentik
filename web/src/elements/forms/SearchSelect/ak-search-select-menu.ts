import { AKElement } from "@goauthentik/elements/Base.js";
import { bound } from "@goauthentik/elements/decorators/bound.js";

import { PropertyValues, css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { Ref, createRef, ref } from "lit/directives/ref.js";

import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";
import PFSelect from "@patternfly/patternfly/components/Select/select.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { AkKeyboardController } from "./SearchKeyboardController.js";
import { KeyboardControllerEscapeEvent, KeyboardControllerSelectEvent } from "./SearchKeyboardControllerEvents.js";
import {
    SearchSelectMenuLostFocusEvent,
    SearchSelectRequestCloseEvent,
    SearchSelectSelectItemEvent,
} from "./SearchSelectEvents.js";
import type { GroupedOptions, SearchGroup, SearchOptions, SearchTuple } from "./types.js";

type ValuedHtmlElement = HTMLElement & { value: string };

/*
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
     *
     * @prop
     */
    @property({ type: Object, attribute: false })
    host!: HTMLElement;

    /**
     * See the search options type, described in the `./types` file, for the relevant types.
     *
     * @prop
     */
    @property({ type: Array, attribute: false })
    options: SearchOptions = [];

    /**
     * The current value of the menu.
     *
     * @prop
     */
    @property()
    value?: string;

    /**
     * The string representation that means an empty option. If not present, no empty option is
     * possible.
     *
     * @prop
     */
    @property()
    emptyOption?: string;

    /**
     * Controlled by the parent, dictates if the menu is open.
     *
     * @prop
     */
    @property({ type: Boolean, reflect: true })
    open = false;

    private keyboardController: AkKeyboardController;

    constructor() {
        super();
        this.keyboardController = new AkKeyboardController(this);
        this.addEventListener(KeyboardControllerSelectEvent.eventName, this.onKeySelect);
        this.addEventListener(KeyboardControllerEscapeEvent.eventName, this.onKeyClose);
    }

    // Handles the "easy mode" of just passing an array of tuples.
    fixedOptions(): GroupedOptions {
        return Array.isArray(this.options) ? { grouped: false, options: this.options } : this.options;
    }

    get items(): ValuedHtmlElement[] {
        return Array.from(this.renderRoot.querySelectorAll(".ak-select-item"));
    }

    @bound
    onClick(event: Event, value: string) {
        event.stopPropagation();
        this.host.dispatchEvent(new SearchSelectSelectItemEvent(value));
        this.value = value;
    }

    @bound
    onEmptyClick(event: Event) {
        event.stopPropagation();
        this.host.dispatchEvent(new SearchSelectSelectItemEvent(undefined));
        this.value = undefined;
    }

    @bound
    onKeySelect(event: KeyboardControllerSelectEvent) {
        event.stopPropagation();
        this.value = event.value;
        this.host.dispatchEvent(new SearchSelectSelectItemEvent(this.value));
    }

    @bound
    onKeyClose(event: KeyboardControllerEscapeEvent) {
        event.stopPropagation();
        this.host.dispatchEvent(new SearchSelectRequestCloseEvent());
    }

    get hasFocus() {
        return this.renderRoot.contains(document.activeElement) || document.activeElement === this;
    }

    @bound
    onLostFocus(event: FocusEvent) {
        event.stopPropagation();
        window.setTimeout(() => {
            if (!this.hasFocus) {
                this.host.dispatchEvent(new SearchSelectMenuLostFocusEvent());
            }
        }, 0);
    }

    updated(changed: PropertyValues<this>) {
        if (changed.has("open") && this.open) {
            this.keyboardController.hostVisible();
        }
    }

    renderEmptyMenuItem() {
        return html`<li>
            <button class="pf-c-dropdown__menu-item" role="option" tabindex="0" @click=${this.onEmptyClick}>
                ${this.emptyOption}
            </button>
        </li>`;
    }

    renderMenuItems(options: SearchTuple[]) {
        return options.map(
            ([value, label, desc]: SearchTuple) => html`
                <li value=${value}>
                    <button
                        class="pf-c-dropdown__menu-item pf-m-description ak-select-item"
                        role="option"
                        value=${value}
                        tabindex="0"
                        @click=${(ev: Event) => {
                            this.onClick(ev, value);
                        }}
                    >
                        <div class="pf-c-dropdown__menu-item-main">${label}</div>
                        ${desc ? html`<div class="pf-c-dropdown__menu-item-description">${desc}</div>` : nothing}
                    </button>
                </li>
            `
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
            `
        );
    }

    render() {
        const options = this.fixedOptions();
        return html`<div class="pf-c-dropdown pf-m-expanded" tabindex="1" @focusout=${this.onLostFocus}>
            <ul class="pf-c-dropdown__menu pf-m-static" role="listbox" tabindex="0">
                ${this.emptyOption !== undefined ? this.renderEmptyMenuItem() : nothing}
                ${options.grouped ? this.renderMenuGroups(options.options) : this.renderMenuItems(options.options)}
            </ul>
        </div> `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-search-select-menu": SearchSelectMenu;
    }
}

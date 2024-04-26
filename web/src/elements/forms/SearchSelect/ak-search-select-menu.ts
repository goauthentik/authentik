import { AKElement } from "@goauthentik/elements/Base.js";
import { bound } from "@goauthentik/elements/decorators/bound.js";

import {
    ReactiveController,
    ReactiveControllerHost,
    TemplateResult,
    css,
    html,
    nothing,
} from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";
import PFSelect from "@patternfly/patternfly/components/Select/select.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { AkKeyboardController } from "./SearchKeyboardController";

type SearchPair = [string, string, undefined | string | TemplateResult];
type SearchGroup = { name: string; options: SearchPair[] };

type SearchOptions =
    | {
          grouped: false;
          options: SearchPair[];
      }
    | {
          grouped: true;
          options: SearchGroup[];
      };

export class SearchSelectClickEvent extends Event {
    static EVENT_NAME = "ak-search-select-click";
    value: string | undefined;
    constructor(value: string | undefined) {
        super(SearchSelectClickEvent.EVENT_NAME, { composed: true, bubbles: true });
        this.value = value;
    }
}

/**
 * @class SearchSelectMenu
 * @element ak-search-select-menu
 *
 * The actual renderer of our components. Intended to be positioned and controlled automatically
 * from the outside.
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
                    position: absolute;
                    inset: 0px auto auto 0px;
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

    @property({ type: Object, attribute: false })
    host: HTMLElement;

    @property({ type: Array, attribute: false })
    options: SearchOptions;

    @property()
    value?: string;

    @property()
    emptyOption?: string;

    private keyboardController: AkKeyboardController;

    constructor() {
        super();
        this.keyboardController = new AkKeyboardController(this);
    }

    @bound
    onClick(ev: Event, item: string) {
        ev.stopPropagation();
        this.host.dispatchEvent(new SearchSelectClickEvent(item));
        this.keyboardController.value = item;
    }

    @bound
    onEmptyClick(ev: Event) {
        ev.stopPropagation();
        this.host.dispatchEvent(new SearchSelectClickEvent(undefined));
    }

    renderEmptyMenuItem() {
        return html`<li>
            <button class="pf-c-dropdown__menu-item" role="option" @click=${this.onEmptyClick}>
                ${this.emptyOption}
            </button>
        </li>`;
    }

    renderMenuItems(options: SearchPair[]) {
        return options.map(
            ([value, label, desc]: SearchPair) => html`
                <li>
                    <button
                        class="pf-c-dropdown__menu-item pf-m-description ak-select-item"
                        role="option"
                        value=${value}
                        @click=${(ev) => {
                            this.onClick(ev, value);
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
        return html`<div class="pf-c-dropdown pf-m-expanded">
            <ul class="pf-c-dropdown__menu pf-m-static" role="listbox" tabindex="0">
                ${this.emptyOption !== undefined ? this.renderEmptyOption() : nothing}
                ${this.options.grouped
                    ? this.renderMenuGroups(this.options.options)
                    : this.renderMenuItems(this.options.options)}
            </ul>
        </div> `;
    }
}

declare global {
    interface GlobalEventHandlersEventMap {
        "ak-search-select-click": SearchSelectClickEvent;
    }

    interface HTMLElementTagNameMap {
        "ak-search-select-menu": SearchSelectMenu;
    }
}

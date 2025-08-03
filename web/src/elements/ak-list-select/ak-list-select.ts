import { groupOptions, isVisibleInScrollRegion } from "./utils.js";

import { AKElement } from "#elements/Base";
import type { GroupedOptions, SelectGroup, SelectOption, SelectOptions } from "#elements/types";
import { randomId } from "#elements/utils/randomId";

import { match } from "ts-pattern";

import { css, html, nothing, PropertyValueMap } from "lit";
import { customElement, property, query, state } from "lit/decorators.js";

import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";
import PFSelect from "@patternfly/patternfly/components/Select/select.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

export interface IListSelect {
    options: SelectOptions;
    value?: string | null;
    emptyOption?: string;
}

/**
 * @class ListSelect
 * @element ak-list-select
 *
 * authentik scrolling list select element
 *
 * Provides a menu of elements to be used for selection.
 *
 * - @prop options (SelectOption[]): The options to display.
 * - @attr value (string): the current value of the Component
 * - @attr emptyOption (string): if defined, the component can be `undefined` and will
 *   display this string at the top.
 *
 * - @fires change: When the value of the element has changed
 *
 * - @part ak-list-select-wrapper: the `<div>` that contains the whole
 * - @part ak-list-select: the `<ul>` that defines the list. This is the component
 *   to target if you want to change the max height.
 * - @part ak-list-select-option: The `<li>` items of the list
 * - @part ak-list-select-button: The `<button>` element of an item.
 * - @part ak-list-select-desc: The description element of the list
 * - @part ak-list-select-group: A section of a grouped list.
 * - @part ak-list-select-title: The title of a group
 */
@customElement("ak-list-select")
export class ListSelect extends AKElement implements IListSelect {
    static styles = [
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
                width: 100%;
            }
        `,
    ];

    //#region Properties

    /**
     * See the search options type, described in the `./types` file, for the relevant types.
     *
     * @prop
     */
    @property({ type: Array, attribute: false })
    public set options(options: SelectOptions) {
        this.#options = groupOptions(options);
    }

    public get options() {
        return this.#options;
    }

    #options!: GroupedOptions;

    /**
     * The current value of the menu.
     *
     * @prop
     */
    @property({ type: String, reflect: true })
    public value?: string | null = null;

    /**
     * The string representation that means an empty option. If not present, no empty option is
     * possible.
     *
     * @prop
     */
    @property()
    public emptyOption?: string;

    // We have two different states that we're tracking in this component: the `value`, which is the
    // element that is currently selected according to the client, and the `index`, which is the
    // element that is being tracked for keyboard interaction. On a click, the index points to the
    // value element; on Keyup.Enter, the value becomes whatever the index points to.
    @state()
    protected indexOfFocusedItem = 0;

    @query("#ak-list-select-list")
    protected ul!: HTMLUListElement;

    //#endregion

    get json(): string {
        return this.value ?? "";
    }

    //#region Lifecycle

    public override connectedCallback() {
        super.connectedCallback();

        this.addEventListener("focus", this.#focusListener);
        this.addEventListener("blur", this.#blurListener);

        this.setAttribute("data-ouia-component-type", "ak-menu-select");
        this.setAttribute("data-ouia-component-id", this.getAttribute("id") || randomId());
        this.setIndexOfFocusedItemFromValue();
        this.highlightFocusedItem();
    }

    public override disconnectedCallback() {
        super.disconnectedCallback();

        this.removeEventListener("focus", this.#focusListener);
        this.removeEventListener("blur", this.#blurListener);
    }

    public override performUpdate() {
        this.removeAttribute("data-ouia-component-safe");
        super.performUpdate();
    }

    public override updated(changed: PropertyValueMap<this>) {
        super.updated(changed);
        this.setAttribute("data-ouia-component-safe", "true");
    }

    //#endregion

    public get hasFocus() {
        return this.renderRoot.contains(document.activeElement) || document.activeElement === this;
    }

    private get displayedElements(): HTMLElement[] {
        return Array.from(this.renderRoot.querySelectorAll(".ak-select-item"));
    }

    public get currentElement(): HTMLElement | undefined {
        const curIndex = this.indexOfFocusedItem;
        return curIndex < 0 || curIndex > this.displayedElements.length - 1
            ? undefined
            : this.displayedElements[curIndex];
    }

    private setIndexOfFocusedItemFromValue() {
        const index = this.displayedElements.findIndex((element) => {
            return element.getAttribute("value") === this.value;
        });
        const elementCount = this.displayedElements.length;

        const checkIndex = () => (index === -1 ? 0 : index);
        return elementCount === 0 ? -1 : checkIndex();
    }

    private highlightFocusedItem() {
        this.displayedElements.forEach((item) => {
            item.classList.remove("ak-highlight-item");
            item.removeAttribute("aria-selected");
            item.tabIndex = -1;
        });
        const currentElement = this.currentElement;
        if (!currentElement) {
            return;
        }
        currentElement.classList.add("ak-highlight-item");
        // This is currently a radio emulation; "selected" is true here.
        // If this were a checkbox emulation (i.e. multi), "checked" would be appropriate.
        currentElement.setAttribute("aria-selected", "true");
        currentElement.scrollIntoView({ block: "center", behavior: "smooth" });
    }

    //#region Event Listeners

    #focusListener = () => {
        // Allow the event to propagate.
        this.currentElement?.focus();
        this.addEventListener("keyup", this.#delegateKey);
    };

    #blurListener = () => {
        // Allow the event to propagate.
        this.removeEventListener("keyup", this.#delegateKey);
        this.indexOfFocusedItem = 0;
    };

    #clickListener = (value: string | null) => {
        // let the click through, but include the change event.
        this.value = value;

        this.setIndexOfFocusedItemFromValue();
        this.dispatchEvent(new Event("change", { bubbles: true, composed: true }));
    };

    #delegateKey = (event: KeyboardEvent) => {
        const key = event.key;
        const lastItem = this.displayedElements.length - 1;
        const current = this.indexOfFocusedItem;

        const updateIndex = (pos: number) => {
            event.preventDefault();
            this.indexOfFocusedItem = pos;
            this.highlightFocusedItem();
            this.currentElement?.focus();
        };

        const setValueAndDispatch = () => {
            event.preventDefault();
            this.value = this.currentElement?.getAttribute("value");

            this.dispatchEvent(new Event("change", { bubbles: true, composed: true }));
        };

        const pageBy = (direction: number) => {
            const visibleElementCount =
                this.displayedElements.filter((element) =>
                    isVisibleInScrollRegion(element, this.ul),
                ).length - 1;
            return visibleElementCount * direction + current;
        };

        match({ key })
            .with({ key: "ArrowDown" }, () => updateIndex(Math.min(current + 1, lastItem)))
            .with({ key: "ArrowUp" }, () => updateIndex(Math.max(current - 1, 0)))
            .with({ key: "PageDown" }, () => updateIndex(Math.min(pageBy(1), lastItem)))
            .with({ key: "PageUp" }, () => updateIndex(Math.max(pageBy(-1), 0)))
            .with({ key: "Home" }, () => updateIndex(0))
            .with({ key: "End" }, () => updateIndex(lastItem))
            .with({ key: " " }, () => setValueAndDispatch())
            .with({ key: "Enter" }, () => setValueAndDispatch());
    };

    //#region Render

    private renderEmptyMenuItem() {
        return html`<li role="option" class="ak-select-item" part="ak-list-select-option">
            <button
                class="pf-c-dropdown__menu-item"
                role="option"
                tabindex="0"
                @click=${() => this.#clickListener(null)}
                part="ak-list-select-button"
            >
                ${this.emptyOption}
            </button>
        </li>`;
    }

    private renderMenuItems(options: SelectOption[]) {
        return options.map(
            ([value, label, desc]: SelectOption) => html`
                <li
                    role="option"
                    value=${value}
                    class="ak-select-item"
                    part="ak-list-select-option"
                >
                    <button
                        class="pf-c-dropdown__menu-item pf-m-description"
                        value="${value}"
                        tabindex="0"
                        @click=${() => this.#clickListener(value)}
                        part="ak-list-select-button"
                    >
                        <div class="pf-c-dropdown__menu-item-main" part="ak-list-select-label">
                            ${label}
                        </div>
                        ${desc
                            ? html`<div
                                  class="pf-c-dropdown__menu-item-description"
                                  part="ak-list-select-desc"
                              >
                                  ${desc}
                              </div>`
                            : nothing}
                    </button>
                </li>
            `,
        );
    }

    private renderMenuGroups(optionGroups: SelectGroup[]) {
        return optionGroups.map(
            ({ name, options }) => html`
                <section class="pf-c-dropdown__group" part="ak-list-select-group">
                    <h1 class="pf-c-dropdown__group-title" part="ak-list-select-group-title">
                        ${name}
                    </h1>
                    <ul>
                        ${this.renderMenuItems(options)}
                    </ul>
                </section>
            `,
        );
    }

    public override render() {
        return html`<div
            class="pf-c-dropdown pf-m-expanded"
            tabindex="1"
            part="ak-list-select-wrapper"
        >
            <ul
                class="pf-c-dropdown__menu pf-m-static"
                id="ak-list-select-list"
                role="listbox"
                tabindex="0"
                part="ak-list-select"
            >
                ${this.emptyOption ? this.renderEmptyMenuItem() : nothing}
                ${this.#options.grouped
                    ? this.renderMenuGroups(this.#options.options)
                    : this.renderMenuItems(this.#options.options)}
            </ul>
        </div> `;
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-list-select": ListSelect;
    }
}

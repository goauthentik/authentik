import { AKElement } from "@goauthentik/elements/Base.js";
import { bound } from "@goauthentik/elements/decorators/bound.js";
import { match } from "ts-pattern";

import { PropertyValues, css, html, nothing } from "lit";
import { customElement, property, query, state } from "lit/decorators.js";

import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";
import PFSelect from "@patternfly/patternfly/components/Select/select.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { isVisibleInScrollRegion } from "./utils.js";

/**
 * Authentik menu element
 *
 * Provides a menu of elements to be used for selection.
 *
 * - @fires change: When the value of the element has changed
 */
@customElement("ak-list-select")
export class ListSelect extends AKElement {
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
                    width: 100%;
                }
            `,
        ];
    }

    /**
     * See the search options type, described in the `./types` file, for the relevant types.
     *
     * @prop
     */
    @property({ type: Array, reflect: false })
    options: AkSelectOption[] = [];

    /**
     * The current value of the menu.
     *
     * @prop
     */
    @property({ type: String, reflect: true })
    value?: string;

    /**
     * The string representation that means an empty option. If not present, no empty option is
     * possible.
     *
     * @prop
     */
    @property()
    emptyOption?: string;

    // We have two different states that we're tracking in this component: the `value`, which is the
    // element that is currently selected according to the client, and the `index`, which is the
    // element that is being tracked for keyboard interaction. On a click, the index points to the
    // value element; on Keydown.Enter, the value becomes whatever the index points to.
    @state()
    indexOfFocusedItem = -1;

    @query("#ak-list-select-list")
    ul!: HTMLUListElement;

    eventTarget: HTMLElement;

    public constructor() {
        super();
        this.addEventListener("focusin", this.onFocus);
        this.addEventListener("blur", this.onBlur);
    }

    @bound
    onFocus() {
        // Allow the event to propagate.
        this.currentElement?.focus();
        this.addEventListener("keydown", this.onKeydown);
    }

    @bound
    onBlur() {
        // Allow the event to propagate.
        this.removeEventListener("keydown", this.onKeydown);
    }

    @bound
    onClick(value: string) {
        this.value = value;
        this.setIndexOfFocusedItemFromValue();
        this.dispatchEvent(new Event("change", { bubbles: true, composed: true })); // prettier-ignore
    }

    @bound
    onKeydown(event: KeyboardEvent) {
        const key = event.key;
        const lastItem = this.displayedElements.length - 1;
        const current = this.indexOfFocusedItem;

        const updateItem = (pos: number) => {
            this.indexOfFocusedItem = pos;
            this.highlightFocusedItem();
        };

        const setValueAndDispatch = () => {
            this.value = this.currentElement.getAttribute("value");
            this.dispatchEvent(new Event("change", { bubbles: true, composed: true })); // prettier-ignore
        };

        const pageKey = (direction: number) => {
            const visibleElementCount =
                this.displayedElements.filter((element) => isVisibleInScrollRegion(element, this.ul)).length - 1; // prettier-ignore

            return visibleElementCount * direction + current;
        };

        let preventDefault = true;
        match({ key })
            .with({ key: "ArrowDown" }, () => updateItem(Math.min(current + 1, lastItem)))
            .with({ key: "ArrowUp" }, () => updateItem(Math.max(current - 1, 0)))
            .with({ key: "PageDown" }, () => updateItem(Math.min(pageKey(1), lastItem)))
            .with({ key: "PageUp" }, () => updateItem(Math.max(pageKey(-1), 0)))
            .with({ key: "Home" }, () => updateItem(0))
            .with({ key: "End" }, () => updateItem(lastItem))
            .with({ key: " " }, () => setValueAndDispatch())
            .with({ key: "Enter" }, () => setValueAndDispatch())
            .otherwise(() => {
                preventDefault = false;
            });

        if (preventDefault) {
            event.preventDefault();
        }
    }

    private get displayedElements(): HTMLElement[] {
        return Array.from(this.renderRoot.querySelectorAll(".ak-select-item"));
    }

    private get currentElement(): HTMLElement | undefined {
        return this.indexOfFocusedItem === -1
            ? undefined
            : this.displayedElements[this.indexOfFocusedItem];
    }

    // Handles the "easy mode" of just passing an array of tuples.
    private get groupedOptions(): GroupedOptions {
        return Array.isArray(this.options)
            ? { grouped: false, options: this.options }
            : this.options;
    }

    private setIndexOfFocusedItemFromValue() {
        this.indexOfFocusedItem = this.displayedElements.findIndex((element) => {
            return element.getAttribute("value") === this.value;
        });
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
        currentElement.setAttribute("aria-selected", true);
        currentElement.focus();
        currentElement.scrollIntoView({ block: "center", behavior: "smooth" });
    }

    public override connectedCallback() {
        super.connectedCallback();
        this.eventTarget = this.host ?? this;
        this.setAttribute("data-ouia-component-type", "ak-menu-select");
        this.setAttribute("data-ouia-component-id", this.getAttribute("id") || randomId());
        this.setIndexOfFocusedItemFromValue();
        this.highlightFocusedItem();
    }

    public override performUpdate() {
        this.removeAttribute("data-ouia-component-safe");
        super.performUpdate();
    }

    public override updated(...args) {
        super.updated && super.updated(...args);
        this.setAttribute("data-ouia-component-safe", true);
    }

    private renderMenuItems(options: SearchTuple[]) {
        return options.map(
            ([value, label, desc]: SearchTuple) => html`
                <li role="option" value=${value}  class="ak-select-item" part="ak-list-select-option">
                    <button
                        class="pf-c-dropdown__menu-item pf-m-description
                        value=${value}
                        tabindex="0"
                        @click=${() => this.onClick(value)}
                        part="ak-list-select-button"
                    >
                        <div class="pf-c-dropdown__menu-item-main" part="ak-list-select-label">${label}</div>
                        ${
                            desc
                                ? html`<div
                                      class="pf-c-dropdown__menu-item-description"
                                      part="ak-list-select-desc"
                                  >
                                      ${desc}
                                  </div>`
                                : nothing
                        }
                    </button>
                </li>
            `,
        );
    }

    private renderMenuGroups(options: SearchGroup[]) {
        return options.map(
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
        const options = this.groupedOptions;
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
        "ak-list-select": ListSelect;
    }
}

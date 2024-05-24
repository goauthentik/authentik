import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { APIErrorTypes, parseAPIError } from "@goauthentik/common/errors";
import { ascii_letters, digits, groupBy, randomString } from "@goauthentik/common/utils";
import { AKElement } from "@goauthentik/elements/Base";
import { PreventFormSubmit } from "@goauthentik/elements/forms/helpers";
import { ensureCSSStyleSheet } from "@goauthentik/elements/utils/ensureCSSStyleSheet";
import { CustomEmitterElement } from "@goauthentik/elements/utils/eventEmitter";

import { msg, str } from "@lit/localize";
import { TemplateResult, html, render } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { styleMap } from "lit/directives/style-map.js";

import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFSelect from "@patternfly/patternfly/components/Select/select.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { ResponseError } from "@goauthentik/api";

type Group<T> = [string, T[]];

@customElement("ak-search-select")
export class SearchSelect<T> extends CustomEmitterElement(AKElement) {
    // A function which takes the query state object (accepting that it may be empty) and returns a
    // new collection of objects.
    @property({ attribute: false })
    fetchObjects!: (query?: string) => Promise<T[]>;

    // A function passed to this object that extracts a string representation of items of the
    // collection under search.
    @property({ attribute: false })
    renderElement!: (element: T) => string;

    // A function passed to this object that extracts an HTML representation of additional
    // information for items of the collection under search.
    @property({ attribute: false })
    renderDescription?: (element: T) => TemplateResult;

    // A function which returns the currently selected object's primary key, used for serialization
    // into forms.
    @property({ attribute: false })
    value!: (element: T | undefined) => unknown;

    // A function passed to this object that determines an object in the collection under search
    // should be automatically selected. Only used when the search itself is responsible for
    // fetching the data; sets an initial default value.
    @property({ attribute: false })
    selected?: (element: T, elements: T[]) => boolean;

    // A function passed to this object (or using the default below) that groups objects in the
    // collection under search into categories.
    @property({ attribute: false })
    groupBy: (items: T[]) => [string, T[]][] = (items: T[]): [string, T[]][] => {
        return groupBy(items, () => {
            return "";
        });
    };

    // Whether or not the dropdown component can be left blank
    @property({ type: Boolean })
    blankable = false;

    // An initial string to filter the search contents, and the value of the input which further
    // serves to restrict the search
    @property()
    query?: string;

    // The objects currently available under search
    @property({ attribute: false })
    objects?: T[];

    // The currently selected object
    @property({ attribute: false })
    selectedObject?: T;

    // Not used in this object. No known purpose.
    @property()
    name?: string;

    // Whether or not the dropdown component is visible.
    @property({ type: Boolean })
    open = false;

    // The textual placeholder for the search's <input> object, if currently empty. Used as the
    // native <input> object's `placeholder` field.
    @property()
    placeholder: string = msg("Select an object.");

    // A textual string representing "The user has affirmed they want to leave the selection blank."
    // Only used if `blankable` above is true.
    @property()
    emptyOption = "---------";

    // Handle the behavior of the drop-down when the :host scrolls off the page.
    scrollHandler?: () => void;
    observer: IntersectionObserver;

    // Handle communication between the :host and the portal
    dropdownUID: string;
    dropdownContainer: HTMLDivElement;

    isFetchingData = false;

    @state()
    error?: APIErrorTypes;

    static get styles() {
        return [PFBase, PFForm, PFFormControl, PFSelect];
    }

    constructor() {
        super();
        if (!document.adoptedStyleSheets.includes(PFDropdown)) {
            document.adoptedStyleSheets = [
                ...document.adoptedStyleSheets,
                ensureCSSStyleSheet(PFDropdown),
            ];
        }
        this.dropdownContainer = document.createElement("div");
        this.observer = new IntersectionObserver(() => {
            this.open = false;
            this.shadowRoot
                ?.querySelectorAll<HTMLInputElement>(
                    ".pf-c-form-control.pf-c-select__toggle-typeahead",
                )
                .forEach((input) => {
                    input.blur();
                });
        });
        this.observer.observe(this);
        this.dropdownUID = `dropdown-${randomString(10, ascii_letters + digits)}`;
        this.onMenuItemClick = this.onMenuItemClick.bind(this);
        this.renderWithMenuGroupTitle = this.renderWithMenuGroupTitle.bind(this);
    }

    toForm(): unknown {
        if (!this.objects) {
            throw new PreventFormSubmit(msg("Loading options..."));
        }
        return this.value(this.selectedObject) || "";
    }

    firstUpdated(): void {
        this.updateData();
    }

    updateData(): void {
        if (this.isFetchingData) {
            return;
        }
        this.isFetchingData = true;
        this.fetchObjects(this.query)
            .then((objects) => {
                objects.forEach((obj) => {
                    if (this.selected && this.selected(obj, objects || [])) {
                        this.selectedObject = obj;
                        this.dispatchCustomEvent("ak-change", { value: this.selectedObject });
                    }
                });
                this.objects = objects;
                this.isFetchingData = false;
            })
            .catch((exc: ResponseError) => {
                this.isFetchingData = false;
                this.objects = undefined;
                parseAPIError(exc).then((err) => {
                    this.error = err;
                });
            });
    }

    connectedCallback(): void {
        super.connectedCallback();
        this.dropdownContainer = document.createElement("div");
        this.dropdownContainer.dataset["managedBy"] = "ak-search-select";
        if (this.name) {
            this.dropdownContainer.dataset["managedFor"] = this.name;
        }
        document.body.append(this.dropdownContainer);
        this.updateData();
        this.addEventListener(EVENT_REFRESH, this.updateData);
        this.scrollHandler = () => {
            this.requestUpdate();
        };
        window.addEventListener("scroll", this.scrollHandler);
    }

    disconnectedCallback(): void {
        super.disconnectedCallback();
        this.removeEventListener(EVENT_REFRESH, this.updateData);
        if (this.scrollHandler) {
            window.removeEventListener("scroll", this.scrollHandler);
        }
        this.dropdownContainer.remove();
        this.observer.disconnect();
    }

    renderMenuItemWithDescription(obj: T, desc: TemplateResult, index: number) {
        return html`
            <li>
                <button
                    class="pf-c-dropdown__menu-item pf-m-description"
                    role="option"
                    @click=${this.onMenuItemClick(obj)}
                    tabindex=${index}
                >
                    <div class="pf-c-dropdown__menu-item-main">${this.renderElement(obj)}</div>
                    <div class="pf-c-dropdown__menu-item-description">${desc}</div>
                </button>
            </li>
        `;
    }

    renderMenuItemWithoutDescription(obj: T, index: number) {
        return html`
            <li>
                <button
                    class="pf-c-dropdown__menu-item"
                    role="option"
                    @click=${this.onMenuItemClick(obj)}
                    tabindex=${index}
                >
                    ${this.renderElement(obj)}
                </button>
            </li>
        `;
    }

    renderEmptyMenuItem() {
        return html`<li>
            <button
                class="pf-c-dropdown__menu-item"
                role="option"
                @click=${this.onMenuItemClick(undefined)}
                tabindex="0"
            >
                ${this.emptyOption}
            </button>
        </li>`;
    }

    onMenuItemClick(obj: T | undefined) {
        return () => {
            this.selectedObject = obj;
            this.dispatchCustomEvent("ak-change", { value: this.selectedObject });
            this.open = false;
        };
    }

    renderMenuGroup(items: T[], tabIndexStart: number) {
        const renderedItems = items.map((obj, index) => {
            const desc = this.renderDescription ? this.renderDescription(obj) : null;
            const tabIndex = index + tabIndexStart;
            return desc
                ? this.renderMenuItemWithDescription(obj, desc, tabIndex)
                : this.renderMenuItemWithoutDescription(obj, tabIndex);
        });
        return html`${renderedItems}`;
    }

    renderWithMenuGroupTitle([group, items]: Group<T>, idx: number) {
        return html`
            <section class="pf-c-dropdown__group">
                <h1 class="pf-c-dropdown__group-title">${group}</h1>
                <ul>
                    ${this.renderMenuGroup(items, idx)}
                </ul>
            </section>
        `;
    }

    get groupedItems(): [boolean, Group<T>[]] {
        const items = this.groupBy(this.objects || []);
        if (items.length === 0) {
            return [false, [["", []]]];
        }
        if (items.length === 1 && (items[0].length < 1 || items[0][0] === "")) {
            return [false, items];
        }
        return [true, items];
    }

    /*
     * This is a little bit hacky. Because we mainly want to use this field in modal-based forms,
     * rendering this menu inline makes the menu not overlay over top of the modal, and cause
     * the modal to scroll.
     * Hence, we render the menu into the document root, hide it when this menu isn't open
     * and remove it on disconnect
     * Also to move it to the correct position we're getting this elements's position and use that
     * to position the menu
     * The other downside this has is that, since we're rendering outside of a shadow root,
     * the pf-c-dropdown CSS needs to be loaded on the body.
     */

    renderMenu(): void {
        if (!this.objects) {
            return;
        }
        const [shouldRenderGroups, groupedItems] = this.groupedItems;

        const pos = this.getBoundingClientRect();
        const position = {
            "position": "fixed",
            "inset": "0px auto auto 0px",
            "z-index": "9999",
            "transform": `translate(${pos.x}px, ${pos.y + this.offsetHeight}px)`,
            "width": `${pos.width}px`,
            ...(this.open ? {} : { visibility: "hidden" }),
        };

        render(
            html`<div style=${styleMap(position)} class="pf-c-dropdown pf-m-expanded">
                <ul
                    class="pf-c-dropdown__menu pf-m-static"
                    role="listbox"
                    style="max-height:50vh;overflow-y:auto;"
                    id=${this.dropdownUID}
                    tabindex="0"
                >
                    ${this.blankable ? this.renderEmptyMenuItem() : html``}
                    ${shouldRenderGroups
                        ? html`${groupedItems.map(this.renderWithMenuGroupTitle)}`
                        : html`${this.renderMenuGroup(groupedItems[0][1], 0)}`}
                </ul>
            </div>`,
            this.dropdownContainer,
            { host: this },
        );
    }

    get renderedValue() {
        if (this.error) {
            return msg(str`Failed to fetch objects: ${this.error.detail}`);
        }
        if (!this.objects) {
            return msg("Loading...");
        }
        if (this.selectedObject) {
            return this.renderElement(this.selectedObject);
        }
        if (this.blankable) {
            return this.emptyOption;
        }
        return "";
    }

    render(): TemplateResult {
        this.renderMenu();

        const onFocus = (ev: FocusEvent) => {
            this.open = true;
            this.renderMenu();
            if (this.blankable && this.renderedValue === this.emptyOption) {
                if (ev.target && ev.target instanceof HTMLInputElement) {
                    ev.target.value = "";
                }
            }
        };

        const onInput = (ev: InputEvent) => {
            this.query = (ev.target as HTMLInputElement).value;
            this.updateData();
        };

        const onBlur = (ev: FocusEvent) => {
            // For Safari, we get the <ul> element itself here when clicking on one of
            // it's buttons, as the container has tabindex set
            if (ev.relatedTarget && (ev.relatedTarget as HTMLElement).id === this.dropdownUID) {
                return;
            }
            // Check if we're losing focus to one of our dropdown items, and if such don't blur
            if (ev.relatedTarget instanceof HTMLButtonElement) {
                const parentMenu = ev.relatedTarget.closest("ul.pf-c-dropdown__menu.pf-m-static");
                if (parentMenu && parentMenu.id === this.dropdownUID) {
                    return;
                }
            }
            this.open = false;
            this.renderMenu();
        };

        return html`<div class="pf-c-select">
            <div class="pf-c-select__toggle pf-m-typeahead">
                <div class="pf-c-select__toggle-wrapper">
                    <input
                        class="pf-c-form-control pf-c-select__toggle-typeahead"
                        type="text"
                        placeholder=${this.placeholder}
                        spellcheck="false"
                        @input=${onInput}
                        @focus=${onFocus}
                        @blur=${onBlur}
                        .value=${this.renderedValue}
                    />
                </div>
            </div>
        </div>`;
    }
}

export default SearchSelect;

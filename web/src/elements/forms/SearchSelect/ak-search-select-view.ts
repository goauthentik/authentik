import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { APIErrorTypes, parseAPIError } from "@goauthentik/common/errors";
import { ascii_letters, digits, groupBy, randomString } from "@goauthentik/common/utils";
import { AKElement } from "@goauthentik/elements/Base";
import { bound } from "@goauthentik/elements/decorators/bound.js";
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

@customElement("ak-search-select")
export class SearchSelectView extends CustomEmitterElement(AKElement) {
    @property({ type: Array, attribute: false })
    options: [boolean, Group<T>[]] = [];

    @property()
    value?: string;

    // Whether or not the dropdown component can be left blank
    @property({ type: Boolean })
    blankable = false;

    // The name of this component as sent to a form
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

    static get styles() {
        return [
            PFBase,
            PFForm,
            PFFormControl,
            PFSelect,
            css`
                :host {
                    overflow: visible;
                }
            `,
        ];
    }

    constructor() {
        super();
        if (!document.adoptedStyleSheets.includes(PFDropdown)) {
            document.adoptedStyleSheets = [
                ...document.adoptedStyleSheets,
                ensureCSSStyleSheet(PFDropdown),
            ];
        }
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
    }

    connectedCallback(): void {
        super.connectedCallback();
        this.dropdownContainer = document.createElement("div");
        this.dropdownContainer.dataset["managedBy"] = "ak-search-select";
        this.name && (this.dropdownContainer.dataset["managedFor"] = this.name);
        document.body.append(this.dropdownContainer);
    }

    disconnectedCallback(): void {
        this.dropdownContainer.remove();
        this.observer.disconnect();
        super.disconnectedCallback();
    }

    @bound
    onMenuItemClick(obj: T | undefined) {
        return () => {
            this.selectedObject = obj;
            this.dispatchCustomEvent("ak-change", { value: this.selectedObject });
            this.open = false;
        };
    }

    @bound
    onFocus(ev: FocusEvent) {
        this.open = true;
        this.renderMenu();
        if (this.blankable && this.renderedValue === this.emptyOption) {
            if (ev.target && ev.target instanceof HTMLInputElement) {
                ev.target.value = "";
            }
        }
    }

    @bound
    onInput(ev: InputEvent) {
        ev.stopPropagation();
        this.dispatchEvent(new SearchSelectQueryEvent((ev.target as HTMLInputElement).value ?? ""));
    }

    @bound
    onBlur(ev: FocusEvent) {
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
    }

    @bound
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
        const pos = this.getBoundingClientRect();
        const position = {
            transform: `translate(${pos.x}px, ${pos.y + this.offsetHeight}px)`,
            width: `${pos.width}px`,
        };

        render(
            html`<ak-search-select-menu
                .options=${this.options}
                .value=${this.value}
                .host=${this}
                .emptyOption=${(this.blankable && this.emptyOption) || undefined}
                ?hidden=${!this.open}
                style=${stylemap(position)}
            ></ak-search-select-menu> `,
            this.dropdownContainer,
        );
    }

    render(): TemplateResult {
        this.renderMenu();

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
                        .value=${this.value ?? ""}
                    />
                </div>
            </div>
        </div>`;
    }
}

export default SearchSelect;

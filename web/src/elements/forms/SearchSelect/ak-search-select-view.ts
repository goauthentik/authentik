import { autoUpdate, computePosition, flip, hide, size } from "@floating-ui/dom";
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
import { Ref, createRef, ref } from "lit/directives/ref.js";
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
    inputRef: Ref<HTMLInputElement> = createRef();

    // Handle communication between the :host and the portal
    dropdownUID: string;
    dropdownContainer: HTMLDivElement;

    // Function to clean up positioned element when we're done.
    public cleanup: () => void;

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

    renderMenu(): void {
        render(
            html`<ak-search-select-menu
                .options=${this.options}
                .value=${this.value}
                .host=${this}
                .emptyOption=${(this.blankable && this.emptyOption) || undefined}
                ?hidden=${!this.open}
            ></ak-search-select-menu> `,
            this.dropdownContainer,
        );

        this.cleanup = autoUpdate(this.inputRef.value, this.dropdownContainer, async () => {
            const { middlewateData, x, y } = await computePosition(
                this.inputRef.value,
                this.dropdownContainer,
                {
                    placement: "bottom",
                    strategy: "fixed",
                    middleware: [flip(), hide()],
                },
            );

            if (middlewareData.hide?.referenceHidden) {
                this.open = false;
                return;
            }

            Object.assign(this.dropdownContainer.style, {
                position: "fixed",
                top: "0",
                left: "0",
                transform: `translate(${x}px, ${y}px)`,
            });
        });
    }

    render(): TemplateResult {
        this.renderMenu();

        return html`<div class="pf-c-select">
            <div class="pf-c-select__toggle pf-m-typeahead">
                <div class="pf-c-select__toggle-wrapper">
                    <input
                        class="pf-c-form-control pf-c-select__toggle-typeahead"
                        type="text"
                        ${this.inputRef}
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

import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { APIErrorTypes, parseAPIError } from "@goauthentik/common/errors";
import { ascii_letters, digits, groupBy, randomString } from "@goauthentik/common/utils";
import { AKElement } from "@goauthentik/elements/Base";
import { PreventFormSubmit } from "@goauthentik/elements/forms/helpers";
import { ensureCSSStyleSheet } from "@goauthentik/elements/utils/ensureCSSStyleSheet";
import { CustomEmitterElement } from "@goauthentik/elements/utils/eventEmitter";

import { msg, str } from "@lit/localize";
import { TemplateResult, css, html, render } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { styleMap } from "lit/directives/style-map.js";

import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFSelect from "@patternfly/patternfly/components/Select/select.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { ResponseError } from "@goauthentik/api";

type Group<T> = [string, T[]];

type ElementRenderer<T> = ((element: T) => string) | keyof T;
type DescriptionRenderer<T> = ((element: T) => TemplateResult | string) | keyof T;
type ValueExtractor<T> = ((element: T) => keyof T) | ((element: undefined) => undefined) | keyof T;

@customElement("ak-search-select")
export class SearchSelect<T extends {}> extends CustomEmitterElement(AKElement) {
    static get styles() {
        return css`
            :host {
                overflow: visible;
            }
        `;
    }

    // A function which takes the query state object (accepting that it may be empty) and returns a
    // new collection of objects.
    @property({ attribute: false })
    fetchObjects!: (query?: string) => Promise<T[]>;

    // An expression passed to this object that extracts a string representation of items of the
    // collection under search. If the expression is a string, it must be a key of the item and will
    // just be rendered as a string.
    @property({ attribute: false })
    renderElement!: ElementRenderer<T>;

    // An expression passed to this object that extracts an HTML representation of additional
    // information for items of the collection under search.  If the expression is a string,
    // it must be a key of the item and will just be rendered as a string.
    @property({ attribute: false })
    renderDescription?: DescriptionRenderer<T>;

    // A function which returns the currently selected object's primary key, used for serialization
    // into forms.
    @property({ attribute: false })
    value!: ValueExtractor<T>;

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

    // The name used by ak-form-element-horizontal to identify this component
    @property()
    name?: string;

    // The textual placeholder for the search's <input> object, if currently empty. Used as the
    // native <input> object's `placeholder` field.
    @property()
    placeholder: string = msg("Select an object.");

    // A textual string representing "The user has affirmed they want to leave the selection blank."
    // Only used if `blankable` above is true.
    @property()
    emptyOption = "---------";

    isFetchingData = false;

    @state()
    error?: APIErrorTypes;

    toForm(): unknown {
        if (!this.objects) {
            throw new PreventFormSubmit(msg("Loading options..."));
        }
        return this.value(this.selectedObject) || "";
    }

    json() {
        return this.toForm();
    }

    firstUpdated(): void {
        this.updateData();
    }

    constructor() {
        super();
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
                        this.dispatchEvent(new InputEvent("input"));
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

    @bound
    onScroll() {
        this.requestUpdate();
    }

    connectedCallback(): void {
        super.connectedCallback();
        window.addEventListener("scroll", this.onScroll);
    }

    disconnectedCallback(): void {
        this.removeEventListener(EVENT_REFRESH, this.updateData);
        window.removeEventListener("scroll", this.onScroll);
        this.dropdownContainer.remove();
        this.observer.disconnect();
        super.disconnectedCallback();
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

    onSearch(e: SearchSelectSearchEvent) {
        e.preventDefault();
        this.query = e.query;
        this.updateData();
    }

    render(): TemplateResult {
        if (this.error) {
            return html`<em>${msg(str(`Failed to fetch objects: ${this.error.detail}`))}</em>`;
        }

        if (!this.objects) {
            return msg("Loading...");
        }

        return html`<ak-search-select-view
            .options=${this.options}
            .value=${this.currentValue}
            ?blankable=${this.blankable}
            name=${this.name}
            placeholder=${this.placeholder}
            emptyOption=${this.emptyOption}
            @ak-search-query=${this.onSearch}
        ></ak-search-select-view> `;
    }
}

export default SearchSelect;

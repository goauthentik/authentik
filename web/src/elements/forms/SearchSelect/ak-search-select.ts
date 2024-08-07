import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { APIErrorTypes, parseAPIError } from "@goauthentik/common/errors";
import { groupBy } from "@goauthentik/common/utils";
import { AkControlElement } from "@goauthentik/elements/AkControlElement.js";
import { PreventFormSubmit } from "@goauthentik/elements/forms/helpers";
import { CustomEmitterElement } from "@goauthentik/elements/utils/eventEmitter";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { ResponseError } from "@goauthentik/api";

import { SearchSelectInputEvent, SearchSelectSelectEvent } from "./SearchSelectEvents.js";
import "./ak-search-select-view.js";
import type { GroupedOptions, SearchGroup, SearchTuple } from "./types.js";

type Group<T> = [string, T[]];

@customElement("ak-search-select")
export class SearchSelect<T> extends CustomEmitterElement(AkControlElement) {
    static get styles() {
        return [PFBase];
    }

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

    // Used to inform the form of the name of the object
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

    async updateData() {
        if (this.isFetchingData) {
            return Promise.resolve();
        }
        this.isFetchingData = true;
        return this.fetchObjects(this.query)
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
        this.dataset.akControl = "true";
        this.updateData();
        this.addEventListener(EVENT_REFRESH, this.updateData);
    }

    disconnectedCallback(): void {
        super.disconnectedCallback();
        this.removeEventListener(EVENT_REFRESH, this.updateData);
    }

    onSearch(event: SearchSelectInputEvent) {
        if (event.value === undefined) {
            this.selectedObject = undefined;
            return;
        }

        this.query = event.value;
        this.updateData()?.then(() => {
            this.dispatchCustomEvent("ak-change", { value: this.selectedObject });
        });
    }

    onSelect(event: SearchSelectSelectEvent) {
        if (event.value === undefined) {
            this.selectedObject = undefined;
            this.dispatchCustomEvent("ak-change", { value: undefined });
            return;
        }
        const selected = (this.objects ?? []).find((obj) => `${this.value(obj)}` === event.value);
        if (!selected) {
            console.warn(
                `ak-search-select: No corresponding object found for value (${event.value}`,
            );
        }
        this.selectedObject = selected;
        this.dispatchCustomEvent("ak-change", { value: this.selectedObject });
    }

    getGroupedItems(): GroupedOptions {
        const items = this.groupBy(this.objects || []);
        const makeSearchTuples = (items: T[]): SearchTuple[] =>
            items.map((item) => [
                `${this.value(item)}`,
                this.renderElement(item),
                this.renderDescription ? this.renderDescription(item) : undefined,
            ]);

        const makeSearchGroups = (items: Group<T>[]): SearchGroup[] =>
            items.map((group) => ({
                name: group[0],
                options: makeSearchTuples(group[1]),
            }));

        if (items.length === 0) {
            return { grouped: false, options: [] };
        }

        if (items.length === 1 && (items[0].length < 1 || items[0][0] === "")) {
            return {
                grouped: false,
                options: makeSearchTuples(items[0][1]),
            };
        }

        return {
            grouped: true,
            options: makeSearchGroups(items),
        };
    }

    render() {
        if (this.error) {
            return html`<em>${msg("Failed to fetch objects: ")} ${this.error.detail}</em>`;
        }

        if (!this.objects) {
            return html`${msg("Loading...")}`;
        }

        const options = this.getGroupedItems();
        const value = this.selectedObject ? `${this.value(this.selectedObject) ?? ""}` : undefined;

        return html`<ak-search-select-view
            .options=${options}
            .value=${value}
            ?blankable=${this.blankable}
            name=${ifDefined(this.name)}
            placeholder=${this.placeholder}
            emptyOption=${ifDefined(this.blankable ? this.emptyOption : undefined)}
            @ak-search-select-input=${this.onSearch}
            @ak-search-select-select=${this.onSelect}
        ></ak-search-select-view> `;
    }
}

export default SearchSelect;

declare global {
    interface HTMLElementTagNameMap {
        "ak-search-select": SearchSelect<unknown>;
    }
}

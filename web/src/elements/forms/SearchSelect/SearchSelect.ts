import { EVENT_REFRESH } from "@goauthentik/common/constants";
import {
    APIError,
    parseAPIResponseError,
    pluckErrorDetail,
} from "@goauthentik/common/errors/network";
import { groupBy } from "@goauthentik/common/utils";
import { AkControlElement } from "@goauthentik/elements/AkControlElement.js";
import { PreventFormSubmit } from "@goauthentik/elements/forms/helpers";
import type { GroupedOptions, SelectGroup, SelectOption } from "@goauthentik/elements/types.js";
import { randomId } from "@goauthentik/elements/utils/randomId.js";

import { msg } from "@lit/localize";
import { PropertyValues, TemplateResult, html } from "lit";
import { property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFBase from "@patternfly/patternfly/patternfly-base.css";

import "./ak-search-select-loading-indicator.js";
import "./ak-search-select-view.js";
import { SearchSelectView } from "./ak-search-select-view.js";

type Group<T> = [string, T[]];

export interface ISearchSelectBase<T> {
    blankable: boolean;
    query?: string;
    objects?: T[];
    selectedObject?: T;
    name?: string;
    placeholder: string;
    emptyOption: string;
}

export class SearchSelectBase<T> extends AkControlElement<string> implements ISearchSelectBase<T> {
    static get styles() {
        return [PFBase];
    }

    // A function which takes the query state object (accepting that it may be empty) and returns a
    // new collection of objects.
    fetchObjects!: (query?: string) => Promise<T[]>;

    // A function passed to this object that extracts a string representation of items of the
    // collection under search.
    renderElement!: (element: T) => string;

    // A function passed to this object that extracts an HTML representation of additional
    // information for items of the collection under search.
    renderDescription?: (element: T) => string | TemplateResult;

    // A function which returns the currently selected object's primary key, used for serialization
    // into forms.
    value!: (element: T | undefined) => string;

    // A function passed to this object that determines an object in the collection under search
    // should be automatically selected. Only used when the search itself is responsible for
    // fetching the data; sets an initial default value.
    selected?: (element: T, elements: T[]) => boolean;

    // A function passed to this object (or using the default below) that groups objects in the
    // collection under search into categories.
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
    error?: APIError;

    public toForm(): string {
        if (!this.objects) {
            throw new PreventFormSubmit(msg("Loading options..."));
        }
        return this.value(this.selectedObject) || "";
    }

    public json() {
        return this.toForm();
    }

    protected dispatchChangeEvent(value: T | undefined) {
        this.dispatchEvent(
            new CustomEvent("ak-change", {
                composed: true,
                bubbles: true,
                detail: { value },
            }),
        );
    }

    public async updateData() {
        if (this.isFetchingData) {
            return Promise.resolve();
        }
        this.isFetchingData = true;
        this.dispatchEvent(new Event("loading"));

        return this.fetchObjects(this.query)
            .then((nextObjects) => {
                nextObjects.forEach((obj) => {
                    if (this.selected && this.selected(obj, nextObjects || [])) {
                        this.selectedObject = obj;
                        this.dispatchChangeEvent(this.selectedObject);
                    }
                });

                this.objects = nextObjects;
                this.isFetchingData = false;
            })
            .catch(async (error: unknown) => {
                this.isFetchingData = false;
                this.objects = undefined;

                const parsedError = await parseAPIResponseError(error);

                this.error = parsedError;
            });
    }

    public override connectedCallback(): void {
        super.connectedCallback();
        this.setAttribute("data-ouia-component-type", "ak-search-select");
        this.setAttribute("data-ouia-component-id", this.getAttribute("id") || randomId());
        this.dataset.akControl = "true";
        this.updateData();
        this.addEventListener(EVENT_REFRESH, this.updateData);
    }

    public override disconnectedCallback(): void {
        super.disconnectedCallback();
        this.removeEventListener(EVENT_REFRESH, this.updateData);
    }

    private onSearch(event: InputEvent) {
        const value = (event.target as SearchSelectView).rawValue;
        if (value === undefined) {
            this.selectedObject = undefined;
            return;
        }

        this.query = value;
        this.updateData()?.then(() => {
            this.dispatchChangeEvent(this.selectedObject);
        });
    }

    private onSelect(event: InputEvent) {
        const value = (event.target as SearchSelectView).value;
        if (value === undefined) {
            this.selectedObject = undefined;
            this.dispatchChangeEvent(undefined);
            return;
        }
        const selected = (this.objects ?? []).find((obj) => `${this.value(obj)}` === value);
        if (!selected) {
            console.warn(`ak-search-select: No corresponding object found for value (${value}`);
        }
        this.selectedObject = selected;
        this.dispatchChangeEvent(this.selectedObject);
    }

    private getGroupedItems(): GroupedOptions {
        const groupedItems = this.groupBy(this.objects || []);

        const makeSearchTuples = (items: T[]): SelectOption[] =>
            items.map((item) => [
                `${this.value(item)}`,
                this.renderElement(item),
                this.renderDescription ? this.renderDescription(item) : undefined,
            ]);

        const makeSearchGroups = (items: Group<T>[]): SelectGroup[] =>
            items.map((group) => ({
                name: group[0],
                options: makeSearchTuples(group[1]),
            }));

        if (groupedItems.length === 0) {
            return { grouped: false, options: [] };
        }

        if (
            groupedItems.length === 1 &&
            (groupedItems[0].length < 1 || groupedItems[0][0] === "")
        ) {
            return {
                grouped: false,
                options: makeSearchTuples(groupedItems[0][1]),
            };
        }

        return {
            grouped: true,
            options: makeSearchGroups(groupedItems),
        };
    }

    public override performUpdate() {
        this.removeAttribute("data-ouia-component-safe");
        super.performUpdate();
    }

    public override render() {
        if (this.error) {
            return html`<em
                >${msg("Failed to fetch objects: ")} ${pluckErrorDetail(this.error)}</em
            >`;
        }

        // `this.objects` is both a container and a sigil; if it is in the `undefined` state, it's a
        // marker that this component has not yet completed a *first* load. After that, it should
        // never be empty. The only state that allows it to be empty after a successful retrieval is
        // a subsequent retrieval failure, in which case `this.error` above will be populated and
        // displayed before this.
        if (!this.objects) {
            return html`<ak-search-select-loading-indicator
                tabindex="-1"
            ></ak-search-select-loading-indicator>`;
        }

        const options = this.getGroupedItems();
        const value = this.selectedObject ? `${this.value(this.selectedObject) ?? ""}` : undefined;

        return html`<ak-search-select-view
            managed
            .options=${options}
            value=${ifDefined(value)}
            ?blankable=${this.blankable}
            name=${ifDefined(this.name)}
            placeholder=${this.placeholder}
            emptyOption=${ifDefined(this.blankable ? this.emptyOption : undefined)}
            @input=${this.onSearch}
            @change=${this.onSelect}
        ></ak-search-select-view> `;
    }

    public override updated(changed: PropertyValues<this>) {
        if (!this.isFetchingData && changed.has("objects")) {
            this.dispatchEvent(new Event("ready"));
        }
        // It is not safe for automated tests to interact with this component while it is fetching
        // data.
        if (!this.isFetchingData) {
            this.setAttribute("data-ouia-component-safe", "true");
        }
    }
}

export default SearchSelectBase;

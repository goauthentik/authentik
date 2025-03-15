import { groupBy } from "@goauthentik/common/utils.js";

import { TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import { type ISearchSelectBase, SearchSelectBase } from "./SearchSelect.js";

export interface ISearchSelect<T> extends ISearchSelectBase<T> {
    fetchObjects: (query?: string) => Promise<T[]>;
    renderElement: (element: T) => string;
    renderDescription?: (element: T) => string | TemplateResult;
    value: (element: T | undefined) => string;
    selected?: (element: T, elements: T[]) => boolean;
    groupBy: (items: T[]) => [string, T[]][];
}

/**
 * @class SearchSelect
 * @element ak-search-select
 *
 * The API layer of  ak-search-select
 *
 * - @prop fetchObjects (Function): The function by which objects are retrieved by the API.
 * - @prop renderElement (Function): A function that can retrieve the string
 *   "label" of the element
 * - @prop renderDescription (Function): A function that can retrieve the string
 *   or TemplateResult "description" of the element
 * - @prop value (Function | string): A function that can retrieve the value (the current
 *   API object's primary key) selected.
 * - @prop selected (Function): A function that retrieves the current "live" value from the
     list of objects fetched by the function above.
 * - @prop groupBy (Function): A function that can group the objects fetched from the API by
     an internal criteria.
 * - @attr blankable (boolean): if true, the component is blankable and can return `undefined`
 * - @attr name (string): The name of the component, for forms
 * - @attr query (string): The current search criteria for fetching objects
 * - @attr placeholder (string): What to show when the input is empty
 * - @attr emptyOption (string): What to show in the menu to indicate "leave this undefined". Only
 *   shown if `blankable`
 * - @attr selectedObject (Object<T>): The current object, or undefined, selected
 *
 *
 * - @fires ak-change - When a value from the collection has been positively chosen, either as a
 *   consequence of the user typing or when selecting from the list.
 *
 */

@customElement("ak-search-select")
export class SearchSelect<T> extends SearchSelectBase<T> implements ISearchSelect<T> {
    static get styles() {
        return [...SearchSelectBase.styles];
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
    renderDescription?: (element: T) => string | TemplateResult;

    // A function which returns the currently selected object's primary key, used for serialization
    // into forms.
    @property({ attribute: false })
    value!: (element: T | undefined) => string;

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
}

export default SearchSelect;

declare global {
    interface HTMLElementTagNameMap {
        "ak-search-select": SearchSelect<unknown>;
    }
}

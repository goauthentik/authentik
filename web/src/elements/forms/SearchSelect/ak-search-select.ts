import { type ISearchSelectBase, SearchSelectBase } from "./SearchSelect.js";

import { groupBy } from "#common/utils";

import { TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

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
    static styles = [...SearchSelectBase.styles];

    @property({ attribute: false })
    public fetchObjects!: (query?: string) => Promise<T[]>;

    @property({ attribute: false })
    public renderElement!: (element: T) => string;

    @property({ attribute: false })
    public renderDescription?: (element: T) => string | TemplateResult;

    @property({ attribute: false })
    public value!: (element?: T) => string;

    @property({ attribute: false })
    public selected?: (element: T, elements: T[]) => boolean;

    @property({ attribute: false })
    public groupBy: (items: T[]) => [string, T[]][] = (items: T[]): [string, T[]][] => {
        return groupBy(items, () => "");
    };
}

export default SearchSelect;

declare global {
    interface HTMLElementTagNameMap {
        "ak-search-select": SearchSelect<unknown>;
    }
}

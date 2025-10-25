import { type ISearchSelectBase, SearchSelectBase } from "./SearchSelect.js";

import { TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

export interface ISearchSelectApi<T> {
    fetchObjects: (query?: string) => Promise<T[]>;
    renderElement: (element: T) => string;
    renderDescription?: (element: T) => string | TemplateResult;
    value: (element: T | null) => string;
    selected?: (element: T, elements: T[]) => boolean;
    groupBy?: (items: T[]) => [string, T[]][];
}

export interface ISearchSelectEz<T> extends ISearchSelectBase<T> {
    config: ISearchSelectApi<T>;
}

/**
 * @class SearchSelectEz
 * @element ak-search-select-ez
 *
 * The API layer of  ak-search-select, now in EZ format!
 *
 * - @prop config (Object): A Record <string, function> that fulfills the API needed by Search
 *   Select to retrieve, filter, group, describe, and return elements.
 * - @attr blankable (boolean): if true, the component is blankable and can return `undefined`
 * - @attr name (string): The name of the component, for forms
 * - @attr query (string): The current search criteria for fetching objects
 * - @attr placeholder (string): What to show when the input is empty
 * - @attr emptyOption (string): What to show in the menu to indicate "leave this undefined". Only
 *   shown if `blankable`
 * - @attr selectedObject (Object<T>): The current object, or undefined, selected
 *
 * ¹ Due to a limitation in the parsing of properties-vs-attributes, these must be defined as
 *   properties, not attributes.  As a consequence, they must be declared in property syntax.
 *   Example:
 *
 *   `.renderElement=${"name"}`
 *
 * - @fires ak-change - When a value from the collection has been positively chosen, either as a
 *   consequence of the user typing or when selecting from the list.
 *
 */

@customElement("ak-search-select-ez")
export class SearchSelectEz<T> extends SearchSelectBase<T> implements ISearchSelectEz<T> {
    static styles = [...SearchSelectBase.styles];

    public fetchObjects!: (query?: string) => Promise<T[]>;
    public renderElement!: (element: T) => string;
    public renderDescription?: ((element: T) => string | TemplateResult) | undefined;
    public value!: (element: T | null) => string;
    public selected?: ((element: T, elements: T[]) => boolean) | undefined;

    @property({ type: Object, attribute: false })
    public config!: ISearchSelectApi<T>;

    public override connectedCallback() {
        this.fetchObjects = this.config.fetchObjects;
        this.renderElement = this.config.renderElement;
        this.renderDescription = this.config.renderDescription;
        this.value = this.config.value;
        this.selected = this.config.selected;

        if (this.config.groupBy) {
            this.groupBy = this.config.groupBy;
        }

        super.connectedCallback();
    }
}

export default SearchSelectEz;

declare global {
    interface HTMLElementTagNameMap {
        "ak-search-select-ez": SearchSelectEz<unknown>;
    }
}

import { DEFAULT_CONFIG } from "#common/api/config";

import { AKElement } from "#elements/Base";
import { SearchSelect } from "#elements/forms/SearchSelect/index";
import { CustomListenerElement } from "#elements/utils/eventEmitter";

import { CoreApi, CoreGroupsListRequest, Group } from "@goauthentik/api";

import { html } from "lit";
import { customElement, property, query } from "lit/decorators.js";

async function fetchObjects(query?: string): Promise<Group[]> {
    const args: CoreGroupsListRequest = {
        ordering: "name",
        includeUsers: false,
    };
    if (query !== undefined) {
        args.search = query;
    }
    const groups = await new CoreApi(DEFAULT_CONFIG).coreGroupsList(args);
    return groups.results;
}

const renderElement = (group: Group): string => group.name;

const renderValue = (group: Group | undefined): string | undefined => group?.pk;

/**
 * Core Group Search
 *
 * @element ak-core-group-search
 *
 * A wrapper around SearchSelect for the 8 search of groups used throughout our code
 * base.  This is one of those "If it's not error-free, at least it's localized to
 * one place" issues.
 *
 */

@customElement("ak-core-group-search")
export class CoreGroupSearch extends CustomListenerElement(AKElement) {
    /**
     * The current group known to the caller.
     *
     * @attr
     */
    @property({ type: String, reflect: true })
    group?: string;

    @query("ak-search-select")
    search!: SearchSelect<Group>;

    @property({ type: String })
    public name?: string | null;

    selectedGroup?: Group;

    constructor() {
        super();
        this.handleSearchUpdate = this.handleSearchUpdate.bind(this);
    }

    get value() {
        return this.selectedGroup ? renderValue(this.selectedGroup) : undefined;
    }

    connectedCallback() {
        super.connectedCallback();
        const horizontalContainer = this.closest("ak-form-element-horizontal[name]");
        if (!horizontalContainer) {
            throw new Error("This search can only be used in a named ak-form-element-horizontal");
        }
        const name = horizontalContainer.getAttribute("name");
        const myName = this.getAttribute("name");
        if (name !== null && name !== myName) {
            this.setAttribute("name", name);
        }
    }

    handleSearchUpdate(ev: CustomEvent) {
        ev.stopPropagation();
        this.selectedGroup = ev.detail.value;
        this.dispatchEvent(new InputEvent("input", { bubbles: true, composed: true }));
    }

    selected = (group: Group) => {
        return this.group === group.pk;
    };

    render() {
        return html`
            <ak-search-select
                .fetchObjects=${fetchObjects}
                .renderElement=${renderElement}
                .value=${renderValue}
                .selected=${this.selected}
                @ak-change=${this.handleSearchUpdate}
                blankable
            >
            </ak-search-select>
        `;
    }
}

export default CoreGroupSearch;

declare global {
    interface HTMLElementTagNameMap {
        "ak-core-group-search": CoreGroupSearch;
    }
}

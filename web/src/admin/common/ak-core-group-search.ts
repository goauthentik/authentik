import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { AKElement } from "@goauthentik/elements/Base";
import { SearchSelect } from "@goauthentik/elements/forms/SearchSelect";
import { CustomListenerElement } from "@goauthentik/elements/utils/eventEmitter";

import { html } from "lit";
import { customElement } from "lit/decorators.js";
import { property, query } from "lit/decorators.js";

import { CoreApi, CoreGroupsListRequest, Group } from "@goauthentik/api";

async function fetchObjects(query?: string): Promise<Group[]> {
    const args: CoreGroupsListRequest = {
        ordering: "name",
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
    name: string | null | undefined;

    selectedGroup?: Group;

    constructor() {
        super();
        this.selected = this.selected.bind(this);
        this.handleSearchUpdate = this.handleSearchUpdate.bind(this);
        this.addCustomListener("ak-change", this.handleSearchUpdate);
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

    selected(group: Group) {
        return this.group === group.pk;
    }

    render() {
        return html`
            <ak-search-select
                .fetchObjects=${fetchObjects}
                .renderElement=${renderElement}
                .value=${renderValue}
                .selected=${this.selected}
                ?blankable=${true}
            >
            </ak-search-select>
        `;
    }
}

export default CoreGroupSearch;

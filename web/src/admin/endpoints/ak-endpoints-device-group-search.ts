import { DEFAULT_CONFIG } from "#common/api/config";

import { AKElement } from "#elements/Base";
import { SearchSelect } from "#elements/forms/SearchSelect/index";
import { CustomListenerElement } from "#elements/utils/eventEmitter";

import { DeviceGroup, EndpointsApi, EndpointsDeviceGroupsListRequest } from "@goauthentik/api";

import { html } from "lit";
import { customElement, property, query } from "lit/decorators.js";

async function fetchObjects(query?: string): Promise<DeviceGroup[]> {
    const args: EndpointsDeviceGroupsListRequest = {
        ordering: "name",
    };
    if (query !== undefined) {
        args.search = query;
    }
    const groups = await new EndpointsApi(DEFAULT_CONFIG).endpointsDeviceGroupsList(args);
    return groups.results;
}

const renderElement = (group: DeviceGroup): string => group.name;

const renderValue = (group: DeviceGroup | undefined): string | undefined => group?.pbmUuid;

/**
 * @element ak-endpoints-device-group-search
 */

@customElement("ak-endpoints-device-group-search")
export class EndpointsDeviceGroupSearch extends CustomListenerElement(AKElement) {
    /**
     * The current group known to the caller.
     *
     * @attr
     */
    @property({ type: String, reflect: true })
    group?: string;

    @query("ak-search-select")
    search!: SearchSelect<DeviceGroup>;

    @property({ type: String })
    public name?: string | null;

    selectedGroup?: DeviceGroup;

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

    selected = (group: DeviceGroup) => {
        return this.group === group.pbmUuid;
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

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-device-group-search": EndpointsDeviceGroupSearch;
    }
}

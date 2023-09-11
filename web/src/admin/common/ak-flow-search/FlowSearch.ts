import { RenderFlowOption } from "@goauthentik/admin/flows/utils";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { AKElement } from "@goauthentik/elements/Base";
import { SearchSelect } from "@goauthentik/elements/forms/SearchSelect";
import "@goauthentik/elements/forms/SearchSelect";
import { CustomListenerElement } from "@goauthentik/elements/utils/eventEmitter";

import { html } from "lit";
import { property, query } from "lit/decorators.js";

import { FlowsApi, FlowsInstancesListDesignationEnum } from "@goauthentik/api";
import type { Flow, FlowsInstancesListRequest } from "@goauthentik/api";

export function renderElement(flow: Flow) {
    return RenderFlowOption(flow);
}

export function renderDescription(flow: Flow) {
    return html`${flow.slug}`;
}

export function getFlowValue(flow: Flow | undefined): string | undefined {
    return flow?.pk;
}

/**
 * FlowSearch
 *
 * A wrapper around SearchSelect that understands the basic semantics of querying about Flows. This
 * code eliminates the long blocks of unreadable invocation that were embedded in every provider, as well as in
 * sources, tenants, and applications.
 *
 */

export class FlowSearch<T extends Flow> extends CustomListenerElement(AKElement) {
    /**
     * The type of flow we're looking for.
     *
     * @attr
     */
    @property({ type: String })
    flowType?: FlowsInstancesListDesignationEnum;

    /**
     * The id of the current flow, if any. For stages where the flow is already defined.
     *
     * @attr
     */
    @property({ attribute: false })
    currentFlow: string | undefined;

    /**
     * If true, it is not valid to leave the flow blank.
     *
     * @attr
     */
    @property({ type: Boolean })
    required?: boolean = false;

    @query("ak-search-select")
    search!: SearchSelect<T>;

    @property({ type: String })
    name: string | null | undefined;

    selectedFlow?: T;

    get value() {
        return this.selectedFlow ? getFlowValue(this.selectedFlow) : null;
    }

    constructor() {
        super();
        this.fetchObjects = this.fetchObjects.bind(this);
        this.selected = this.selected.bind(this);
        this.handleSearchUpdate = this.handleSearchUpdate.bind(this);
        this.addCustomListener("ak-change", this.handleSearchUpdate);
    }

    handleSearchUpdate(ev: CustomEvent) {
        ev.stopPropagation();
        this.selectedFlow = ev.detail.value;
    }

    async fetchObjects(query?: string): Promise<Flow[]> {
        const args: FlowsInstancesListRequest = {
            ordering: "slug",
            designation: this.flowType,
            ...(query !== undefined ? { search: query } : {}),
        };
        const flows = await new FlowsApi(DEFAULT_CONFIG).flowsInstancesList(args);
        return flows.results;
    }

    /* This is the most commonly overridden method of this class. About half of the Flow Searches
     * use this method, but several have more complex needs, such as relating to the tenant, or just
     * returning false.
     */

    selected(flow: Flow): boolean {
        return this.currentFlow === flow.pk;
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

    render() {
        return html`
            <ak-search-select
                .fetchObjects=${this.fetchObjects}
                .selected=${this.selected}
                .renderElement=${renderElement}
                .renderDescription=${renderDescription}
                .value=${getFlowValue}
                ?blankable=${!this.required}
            >
            </ak-search-select>
        `;
    }
}

export default FlowSearch;

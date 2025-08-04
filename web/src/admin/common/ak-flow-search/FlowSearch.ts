import "#elements/forms/SearchSelect/index";

import { DEFAULT_CONFIG } from "#common/api/config";

import { AKElement } from "#elements/Base";
import { SearchSelect } from "#elements/forms/SearchSelect/index";
import { CustomListenerElement } from "#elements/utils/eventEmitter";

import { RenderFlowOption } from "#admin/flows/utils";

import type { Flow, FlowsInstancesListRequest } from "@goauthentik/api";
import { FlowsApi, FlowsInstancesListDesignationEnum } from "@goauthentik/api";

import { html } from "lit";
import { property, query } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

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
 * sources, brands, and applications.
 *
 */

export class FlowSearch<T extends Flow> extends CustomListenerElement(AKElement) {
    /**
     * The type of flow we're looking for.
     *
     * @attr
     */
    @property({ type: String })
    public flowType?: FlowsInstancesListDesignationEnum;

    /**
     * The id of the current flow, if any. For stages where the flow is already defined.
     *
     * @attr
     */
    @property({ type: String })
    public currentFlow?: string | undefined;

    /**
     * If true, it is not valid to leave the flow blank.
     *
     * @attr
     */
    @property({ type: Boolean })
    public required?: boolean = false;

    @query("ak-search-select")
    protected search!: SearchSelect<T>;

    /**
     * When specified and the object instance does not have a flow selected, auto-select the flow with the given slug.
     *
     * @attr
     */
    @property()
    public defaultFlowSlug?: string;

    @property({ type: String })
    public name: string | null | undefined;

    protected selectedFlow?: T;

    public get value() {
        return this.selectedFlow ? getFlowValue(this.selectedFlow) : null;
    }

    public constructor() {
        super();
        this.fetchObjects = this.fetchObjects.bind(this);
        this.selected = this.selected.bind(this);
        this.handleSearchUpdate = this.handleSearchUpdate.bind(this);
    }

    protected handleSearchUpdate(ev: CustomEvent) {
        ev.stopPropagation();
        this.selectedFlow = ev.detail.value;
        this.dispatchEvent(new InputEvent("input", { bubbles: true, composed: true }));
    }

    protected async fetchObjects(query?: string): Promise<Flow[]> {
        const args: FlowsInstancesListRequest = {
            ordering: "slug",
            designation: this.flowType,
            ...(query !== undefined ? { search: query } : {}),
        };
        const flows = await new FlowsApi(DEFAULT_CONFIG).flowsInstancesList(args);
        return flows.results;
    }

    /* This is the most commonly overridden method of this class. About half of the Flow Searches
     * use this method, but several have more complex needs, such as relating to the brand, or just
     * returning false.
     */
    protected selected(flow: Flow): boolean {
        let selected = this.currentFlow === flow.pk;
        if (!this.currentFlow && this.defaultFlowSlug && flow.slug === this.defaultFlowSlug) {
            selected = true;
        }
        return selected;
    }

    public override connectedCallback() {
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

    public override render() {
        return html`
            <ak-search-select
                .fetchObjects=${this.fetchObjects}
                .selected=${this.selected}
                .renderElement=${renderElement}
                .renderDescription=${renderDescription}
                .value=${getFlowValue}
                name=${ifDefined(this.name ?? undefined)}
                @ak-change=${this.handleSearchUpdate}
                ?blankable=${!this.required}
            >
            </ak-search-select>
        `;
    }
}

export default FlowSearch;

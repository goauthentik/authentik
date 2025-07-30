import "#elements/forms/SearchSelect/index";

import { DEFAULT_CONFIG } from "#common/api/config";

import { AKElement } from "#elements/Base";
import type { HorizontalFormElement } from "#elements/forms/HorizontalFormElement";
import { CustomListenerElement } from "#elements/utils/eventEmitter";

import { RenderFlowOption } from "#admin/flows/utils";

import type { Flow, FlowsInstancesListRequest } from "@goauthentik/api";
import { FlowsApi, FlowsInstancesListDesignationEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { property } from "lit/decorators.js";
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
 */
export abstract class FlowSearch<T extends Flow> extends CustomListenerElement(AKElement) {
    //#region Properties

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
    public currentFlow?: string;

    /**
     * If true, it is not valid to leave the flow blank.
     *
     * @attr
     */
    @property({ type: Boolean })
    public required?: boolean;

    /**
     * When specified and the object instance does not have a flow selected, auto-select the flow with the given slug.
     *
     * @attr
     */
    @property()
    public defaultFlowSlug?: string;

    @property({ type: String })
    public name?: string;

    /**
     * The label of the input, for forms.
     *
     * @attr
     */
    @property({ type: String })
    public label?: string;

    /**
     * The textual placeholder for the search's <input> object, if currently empty. Used as the
     * native <input> object's `placeholder` field.
     *
     * @attr
     */
    @property({ type: String })
    public placeholder = msg("Select a flow...");

    protected selectedFlow?: T;

    get value() {
        return this.selectedFlow ? getFlowValue(this.selectedFlow) : null;
    }

    //#endregion

    //#region Event Listeners

    protected searchUpdateListener = (event: CustomEvent) => {
        event.stopPropagation();

        this.selectedFlow = event.detail.value;

        this.dispatchEvent(new InputEvent("input", { bubbles: true, composed: true }));
    };

    //#endregion

    //#region Lifecycle

    /**
     * Fetch the objects from the API.
     *
     * @param query The search query, if any.
     */
    protected fetchObjects = (query?: string): Promise<Flow[]> => {
        const args: FlowsInstancesListRequest = {
            ordering: "slug",
            designation: this.flowType,
            ...(query ? { search: query } : {}),
        };

        return new FlowsApi(DEFAULT_CONFIG).flowsInstancesList(args).then((flows) => flows.results);
    };

    /**
     * Determine if the flow matches the current state of the search.
     *
     * @param flow The flow to compare against.
     */
    protected match = (flow: Flow): boolean => {
        if (this.currentFlow) {
            return this.currentFlow === flow.pk;
        }

        return !!(this.defaultFlowSlug && flow.slug === this.defaultFlowSlug);
    };

    /**
     * This is the most commonly overridden method of this class.
     *
     *  About half of the Flow Searches use this method, but several have more complex needs,
     * such as relating to the brand, or just returning false.
     *
     * @param flow The flow to compare against.
     * @abstract
     */
    protected selected = (flow: Flow): boolean => {
        return this.match(flow);
    };

    public override connectedCallback() {
        super.connectedCallback();

        const horizontalContainer = this.closest<HorizontalFormElement>(
            "ak-form-element-horizontal[name]",
        );

        if (!horizontalContainer) {
            throw new Error("This search can only be used in a named ak-form-element-horizontal");
        }

        const name = horizontalContainer.getAttribute("name");
        const myName = this.getAttribute("name");

        if (name !== null && name !== myName) {
            this.setAttribute("name", name);
        }
    }

    //#endregion

    //#region Render

    public override render() {
        return html`
            <ak-search-select
                .fetchObjects=${this.fetchObjects}
                .selected=${this.selected}
                .renderElement=${renderElement}
                .renderDescription=${renderDescription}
                .value=${getFlowValue}
                placeholder=${ifDefined(this.placeholder)}
                label=${ifDefined(this.label)}
                name=${ifDefined(this.name)}
                @ak-change=${this.searchUpdateListener}
                ?blankable=${!this.required}
            >
            </ak-search-select>
        `;
    }

    //#endregion
}

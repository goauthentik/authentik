import { customElement, property } from "lit/decorators.js";

import type { Flow } from "@goauthentik/api";

import FlowSearch from "./FlowSearch";

/**
 * Search for flows that may have a fallback specified by the tenant settings
 *
 * @element ak-tenanted-flow-search
 *
 */

@customElement("ak-tenanted-flow-search")
export class AkTenantedFlowSearch<T extends Flow> extends FlowSearch<T> {
    /**
     * The Associated ID of the flow the tenant has, to compare if possible
     *
     * @attr
     */
    @property({ attribute: false, type: String })
    tenantFlow?: string;

    constructor() {
        super();
        this.selected = this.selected.bind(this);
    }

    selected(flow: Flow): boolean {
        return super.selected(flow) || flow.pk === this.tenantFlow;
    }
}

export default AkTenantedFlowSearch;

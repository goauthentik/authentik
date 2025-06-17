import { customElement, property } from "lit/decorators.js";

import type { Flow } from "@goauthentik/api";

import FlowSearch from "./FlowSearch";

/**
 * Search for flows that may have a fallback specified by the brand settings
 *
 * @element ak-branded-flow-search
 *
 */

@customElement("ak-branded-flow-search")
export class AkBrandedFlowSearch<T extends Flow> extends FlowSearch<T> {
    /**
     * The Associated ID of the flow the brand has, to compare if possible
     *
     * @attr
     */
    @property({ attribute: false, type: String })
    brandFlow?: string;

    public selected = (flow: Flow): boolean => {
        return super.selected(flow) || flow.pk === this.brandFlow;
    };
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-branded-flow-search": AkBrandedFlowSearch<Flow>;
    }
}

export default AkBrandedFlowSearch;

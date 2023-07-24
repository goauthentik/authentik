import { customElement } from "lit/decorators.js";
import { property } from "lit/decorators.js";

import type { Flow } from "@goauthentik/api";

import FlowSearch from "./FlowSearch";

/**
 * Search for flows that connect to user sources
 *
 * @element ak-source-flow-search
 *
 */

@customElement("ak-source-flow-search")
export class AkSourceFlowSearch<T extends Flow> extends FlowSearch<T> {
    /**
     * The fallback flow if none specified AND the instance has no set flow and the instance is new.
     *
     * @attr
     */

    @property({ type: String })
    fallback: string | undefined;

    /**
     * The primary key of the Source (not the Flow). Mostly the instancePk itself, used to affirm
     * that we're working on a new stage and so falling back to the default is appropriate.
     *
     * @attr
     */
    @property({ type: String })
    instanceId: string | undefined;

    constructor() {
        super();
        this.selected = this.selected.bind(this);
    }

    // If there's no instance or no currentFlowId for it and the flow resembles the fallback,
    // otherwise defer to the parent class.
    selected(flow: Flow): boolean {
        return (
            (!this.instanceId && !this.currentFlow && flow.slug === this.fallback) ||
            super.selected(flow)
        );
    }
}

export default AkSourceFlowSearch;

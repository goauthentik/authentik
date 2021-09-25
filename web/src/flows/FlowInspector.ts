import { LitElement } from "lit";
import { customElement, property } from "lit/decorators";

import { FlowInspection, FlowsApi } from "@goauthentik/api";

import { DEFAULT_CONFIG } from "../api/Config";
import { EVENT_FLOW_ADVANCE } from "../constants";

@customElement("ak-flow-inspector")
export class FlowInspector extends LitElement {
    flowSlug: string;

    @property({ attribute: false })
    state?: FlowInspection;

    constructor() {
        super();
        this.flowSlug = window.location.pathname.split("/")[3];
    }

    handlerBound = false;

    firstUpdated(): void {
        if (this.handlerBound) return;
        window.addEventListener(EVENT_FLOW_ADVANCE, this.advanceHandler as EventListener);
        this.handlerBound = true;
    }

    disconnectedCallback(): void {
        super.disconnectedCallback();
        window.removeEventListener(EVENT_FLOW_ADVANCE, this.advanceHandler as EventListener);
    }

    advanceHandler = (e: CustomEvent): void => {
        new FlowsApi(DEFAULT_CONFIG)
            .flowsInspectorGet({
                flowSlug: this.flowSlug,
            })
            .then((state) => {
                this.state = state;
            });
    };
}

import "#elements/EmptyState";

import { DEFAULT_CONFIG } from "#common/api/config";

import { Diagram } from "#elements/Diagram";

import { FlowsApi } from "@goauthentik/api";

import { customElement, property } from "lit/decorators.js";

@customElement("ak-flow-diagram")
export class FlowDiagram extends Diagram {
    @property()
    flowSlug?: string;

    refreshHandler = (): void => {
        this.diagram = undefined;
        new FlowsApi(DEFAULT_CONFIG)
            .flowsInstancesDiagramRetrieve({
                slug: this.flowSlug || "",
            })
            .then((data) => {
                this.diagram = data.diagram;
                this.requestUpdate();
            });
    };
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-flow-diagram": FlowDiagram;
    }
}

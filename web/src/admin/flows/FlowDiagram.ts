import "#elements/EmptyState";

import { aki } from "#common/api/client";

import { Diagram } from "#elements/Diagram";

import { FlowsApi } from "@goauthentik/api";

import { customElement, property } from "lit/decorators.js";

@customElement("ak-flow-diagram")
export class FlowDiagram extends Diagram {
    @property({ type: String, useDefault: true })
    flowSlug: string | null = null;

    protected refresh(): void {
        aki(FlowsApi)
            .flowsInstancesDiagramRetrieve({
                slug: this.flowSlug || "",
            })
            .then((data) => {
                this.diagram = data.diagram;
            });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-flow-diagram": FlowDiagram;
    }
}

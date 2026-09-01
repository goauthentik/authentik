import "#elements/EmptyState";

import { buildFlowGraph } from "./FlowGraph";

import { aki } from "#common/api/client";

import { Diagram } from "#elements/Diagram/ak-diagram";

import { DiagramNode, FlowDiagram as FlowDiagramGraph, FlowsApi } from "@goauthentik/api";

import { observes } from "@patternfly/pfe-core/decorators/observes.js";

import { customElement, property } from "lit/decorators.js";

@customElement("ak-flow-diagram")
export class FlowDiagram extends Diagram {
    @property({ type: String, useDefault: true })
    public flowSlug: string | null = null;

    @property({ attribute: false })
    public graph: FlowDiagramGraph | null = null;

    protected nodes: ReadonlyMap<string, DiagramNode> = new Map();

    @observes("flowSlug")
    protected refresh() {
        if (!this.flowSlug) {
            return;
        }

        aki(FlowsApi)
            .flowsInstancesDiagramRetrieve({
                slug: this.flowSlug || "",
            })
            .then((graph) => {
                this.graph = graph;
            });
    }

    @observes("graph")
    protected rebuild() {
        if (!this.graph) {
            return;
        }

        const { diagram, nodes } = buildFlowGraph(this.graph);
        this.nodes = nodes;
        this.diagram = diagram;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-flow-diagram": FlowDiagram;
    }
}

import "#elements/EmptyState";

import { diagramToolbar } from "./FlowDiagramToolbar";
import { buildFlowGraph, isEditableNode, resolveNodeID } from "./FlowGraph";

import { aki } from "#common/api/client";
import { AKRefreshEvent } from "#common/events";

import { listen } from "#elements/decorators/listen";
import { Diagram } from "#elements/Diagram/ak-diagram";

import { DiagramNode, FlowDiagram as FlowDiagramGraph, FlowsApi } from "@goauthentik/api";

import { observes } from "@patternfly/pfe-core/decorators/observes.js";

import { css, render } from "lit";
import { customElement, property, queryAll } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";

const EditIconStyles = css`
    .ak-diagram-toolbar > .pf-c-button {
        box-sizing: border-box;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        inline-size: var(--pf-global--spacer--lg, 1.5rem);
        block-size: var(--pf-global--spacer--lg, 1.5rem);
        padding: 0;
        line-height: 1;
    }
`;

@customElement("ak-flow-diagram")
export class FlowDiagram extends Diagram {
    static styles = [...Diagram.styles, PFButton, EditIconStyles];

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

    // When the flow changes, the diagram must be rebuilt
    @listen(AKRefreshEvent, { target: window })
    protected reload = () => {
        this.refresh();
    };

    @queryAll("g.node[id]")
    svgGroups!: SVGGElement[];

    // Install the toolbar.
    protected override diagramUpdated() {
        for (const group of this.svgGroups) {
            const id = resolveNodeID(group.id);
            const node = id ? this.nodes.get(id) : null;
            if (!(node && isEditableNode(node))) {
                continue;
            }

            const toolbars = group.querySelectorAll<HTMLElement>(".ak-diagram-toolbar");
            const toolbar = toolbars.item(toolbars.length - 1);
            if (!toolbar) {
                continue;
            }

            group.setAttribute("data-ak-node", node.identifier);
            render(diagramToolbar(node), toolbar);
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-flow-diagram": FlowDiagram;
    }
}

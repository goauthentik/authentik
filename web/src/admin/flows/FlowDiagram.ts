import "#elements/EmptyState";
import PFButton from "@patternfly/patternfly/components/Button/button.css";

import { aki } from "#common/api/client";
import { APIError, parseAPIResponseError, pluckErrorDetail } from "#common/errors/network";
import { AKRefreshEvent } from "#common/events";

import { listen } from "#elements/decorators/listen";
import { Diagram } from "#elements/Diagram/ak-diagram";
import { SlottedTemplateResult } from "#elements/types";

import { diagramToolbar } from "#admin/flows/FlowDiagramToolbar";
import { buildFlowGraph, isEditableNode, resolveNodeID } from "#admin/flows/FlowGraph";

import { DiagramNode, FlowDiagram as FlowDiagramGraph, FlowsApi } from "@goauthentik/api";

import { observes } from "@patternfly/pfe-core/decorators/observes.js";

import { msg } from "@lit/localize";
import { css, html, render } from "lit";
import { customElement, property, queryAll, state } from "lit/decorators.js";

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

        --pf-global--Color--200: var(--pf-global--palette--purple-500);
        --pf-global--Color--100: var(--pf-global--palette--purple-600);
    }
`;

@customElement("ak-flow-diagram")
export class FlowDiagram extends Diagram {
    public static override styles = [
        // ---
        ...Diagram.styles,
        PFButton,
        EditIconStyles,
    ];

    @property({ type: String, useDefault: true })
    public flowSlug: string | null = null;

    @property({ attribute: false })
    public graph: FlowDiagramGraph | null = null;

    protected nodes: ReadonlyMap<string, DiagramNode> = new Map();

    @state()
    protected error: APIError | null = null;

    @observes("flowSlug")
    protected refresh(): Promise<void> {
        if (!this.flowSlug) {
            return Promise.resolve();
        }

        return aki(FlowsApi)
            .flowsInstancesDiagramRetrieve({
                slug: this.flowSlug || "",
            })
            .then((graph) => {
                this.error = null;
                this.graph = graph;
            })
            .catch(async (error: unknown) => {
                this.error = await parseAPIResponseError(error);
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

    // A failed refresh keeps the last diagram; the error only replaces the loading placeholder.
    protected override render(): SlottedTemplateResult {
        if (this.error && !this.renderedSVG) {
            return html`<ak-empty-state icon="fa-ban"
                ><span
                    >${msg("Failed to load the flow diagram.", {
                        id: "flow.diagram.load.error",
                    })}</span
                >
                <div slot="body">${pluckErrorDetail(this.error)}</div>
            </ak-empty-state>`;
        }

        return super.render();
    }

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

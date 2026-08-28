import {
    DiagramEdge,
    DiagramEdgeTypeEnum,
    DiagramNode,
    DiagramNodeTypeEnum,
    FlowDiagram,
} from "@goauthentik/api";

import { match } from "ts-pattern";

import { msg, str } from "@lit/localize";

export interface CompiledFlowGraph {
    diagram: string;
    nodes: ReadonlyMap<string, DiagramNode>;
}

/**
 * Mimic the server's hack for including doublequotes
 */
function escapeLabel(label: string): string {
    return label.replaceAll('"', "#quot;");
}

type MermaidShape = (label: string) => string;
const SUBROUTINE = (label: string) => `[["${escapeLabel(label)}"]]`;
const RECTANGLE = (label: string) => `["${escapeLabel(label)}"]`;
const STADIUM = (label: string) => `(["${escapeLabel(label)}"])`;
const HEXAGON = (label: string) => `{{"${escapeLabel(label)}"}}`;

function declaration(id: string, shape: MermaidShape, label: string): string {
    return `${id}${shape(label)}`;
}

function declareNode(node: DiagramNode, id: string): string {
    const { name, verboseName } = node;

    const D = DiagramNodeTypeEnum;
    // prettier-ignore
    return match(node.type)
        .with(D.FlowStart,       () => declaration(id, SUBROUTINE, `${msg("Flow")}\n${name}`))
        .with(D.FlowEnd,         () => declaration(id, SUBROUTINE, msg("End of the flow")))
        .with(D.PreFlowPolicies, () => declaration(id, SUBROUTINE, msg("Pre-flow policies")))
        .with(D.Stage,           () => declaration(id, STADIUM, `${msg(str`Stage (${verboseName})`)}\n${name}`))
        .with(D.Policy,          () => declaration(id, HEXAGON, `${msg(str`Policy (${verboseName})`)}\n${name}`))
        .with(D.AuthenticationRequirement, () => declaration(id, RECTANGLE, `${msg("Flow authentication requirement")}\n${name}`))
        .with(D.UnknownDefaultOpenApi,     () => declaration(id, RECTANGLE, name))
        .exhaustive();
}

function edgeLabel(edge: DiagramEdge, target?: DiagramNode): string {
    const D = DiagramEdgeTypeEnum;
    const order = target?.bindingOrder;

    return match(edge.type)
        .with(D.Proceed, () => "")
        .with(D.PolicyPassed, () => msg("Policy passed"))
        .with(D.PolicyDenied, () => msg("Policy denied"))
        .with(D.RequirementFulfilled, () => msg("Requirement met"))
        .with(D.RequirementUnfulfilled, () => msg("Denied"))
        .with(D.Binding, () => (order ? msg(str`Binding: ${order}`) : ""))
        .with(D.UnknownDefaultOpenApi, () => "")
        .exhaustive();
}

export function compileFlowGraph(graph: FlowDiagram): CompiledFlowGraph {
    const ids = new Map(graph.nodes.map((node, index) => [node.identifier, `n${index}`]));
    const byIdentifier = new Map(graph.nodes.map((node) => [node.identifier, node]));

    const connect = (edge: DiagramEdge): string | null => {
        const source = ids.get(edge.origin);
        const target = ids.get(edge.target);

        if (!source || !target) return null;

        const label = edgeLabel(edge, byIdentifier.get(edge.target));
        const arrow = label ? `--${label}-->` : "-->";

        return `${source} ${arrow} ${target}`;
    };

    const lines = [
        "graph TD",
        ...graph.nodes.map((node, index) => declareNode(node, `n${index}`)),
        ...graph.edges.map(connect).filter((line) => line !== null),
    ];

    const nodes = new Map(graph.nodes.map((node, index) => [`n${index}`, node] as const));
    return {
        diagram: lines.join("\n"),
        nodes,
    };
}

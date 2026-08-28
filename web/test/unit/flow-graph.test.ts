import { compileFlowGraph } from "#admin/flows/FlowGraph";

import {
    DiagramEdge,
    DiagramEdgeTypeEnum,
    DiagramNode,
    DiagramNodeTypeEnum,
    FlowDiagram,
} from "@goauthentik/api";

import { describe, expect, it } from "vitest";

function makeNode(identifier: string, type: DiagramNodeTypeEnum, rest?: Partial<DiagramNode>) {
    return {
        identifier,
        type,
        name: "",
        verboseName: "",
        model: "",
        pk: "",
        component: "",
        bindingModel: "",
        bindingPk: "",
        bindingOrder: null,
        ...rest,
    } satisfies DiagramNode;
}

function makeEdge(
    origin: string,
    target: string,
    type: DiagramEdgeTypeEnum = DiagramEdgeTypeEnum.Proceed,
) {
    return { origin, target, type } satisfies DiagramEdge;
}

function makeGraph(nodes: DiagramNode[], edges: DiagramEdge[]) {
    return { nodes, edges } satisfies FlowDiagram;
}

function compileEdge(type: DiagramEdgeTypeEnum, target?: Partial<DiagramNode>): string {
    const { diagram } = compileFlowGraph(
        makeGraph(
            [
                makeNode("a", DiagramNodeTypeEnum.FlowStart),
                makeNode("b", DiagramNodeTypeEnum.FlowEnd, target),
            ],
            [makeEdge("a", "b", type)],
        ),
    );

    return diagram.split("\n").at(-1)!;
}

describe("compileFlowGraph", () => {
    it("emits a top-down flowchart header for an empty graph", () => {
        const { diagram } = compileFlowGraph(makeGraph([], []));

        expect(diagram).toBe("graph TD");
    });

    it("declares a flow-start node as a subroutine labeled with the flow name", () => {
        const { diagram } = compileFlowGraph(
            makeGraph(
                [
                    makeNode("flow_start", DiagramNodeTypeEnum.FlowStart, {
                        name: "Logged out of application",
                    }),
                ],
                [],
            ),
        );

        expect(diagram).toBe(["graph TD", 'n0[["Flow\nLogged out of application"]]'].join("\n"));
    });

    it("declares a flow-end node as a subroutine labeled with the end of the flow", () => {
        const { diagram } = compileFlowGraph(
            makeGraph([makeNode("done", DiagramNodeTypeEnum.FlowEnd)], []),
        );

        expect(diagram).toBe(["graph TD", 'n0[["End of the flow"]]'].join("\n"));
    });

    it("declares a pre-flow-policies node as a subroutine labeled with the policy phase", () => {
        const { diagram } = compileFlowGraph(
            makeGraph([makeNode("flow_pre", DiagramNodeTypeEnum.PreFlowPolicies)], []),
        );

        expect(diagram).toBe(["graph TD", 'n0[["Pre-flow policies"]]'].join("\n"));
    });

    it("declares an authentication-requirement node as a rectangle labeled with the requirement", () => {
        const { diagram } = compileFlowGraph(
            makeGraph(
                [
                    makeNode(
                        "flow_auth_requirement",
                        DiagramNodeTypeEnum.AuthenticationRequirement,
                        {
                            name: "require_superuser",
                        },
                    ),
                ],
                [],
            ),
        );

        expect(diagram).toBe(
            ["graph TD", 'n0["Flow authentication requirement\nrequire_superuser"]'].join("\n"),
        );
    });

    it("declares a stage node as a stadium labeled with its type and name", () => {
        const { diagram } = compileFlowGraph(
            makeGraph(
                [
                    makeNode("stage_0", DiagramNodeTypeEnum.Stage, {
                        name: "default-authentication-identification",
                        verboseName: "Identification Stage",
                    }),
                ],
                [],
            ),
        );

        expect(diagram).toBe(
            [
                "graph TD",
                'n0(["Stage (Identification Stage)\ndefault-authentication-identification"])',
            ].join("\n"),
        );
    });

    it("declares a policy node as a hexagon labeled with its type and name", () => {
        const { diagram } = compileFlowGraph(
            makeGraph(
                [
                    makeNode("flow_policy_0", DiagramNodeTypeEnum.Policy, {
                        name: "default-oobe-password-usable",
                        verboseName: "Expression Policy",
                    }),
                ],
                [],
            ),
        );

        expect(diagram).toBe(
            ["graph TD", 'n0{{"Policy (Expression Policy)\ndefault-oobe-password-usable"}}'].join(
                "\n",
            ),
        );
    });

    it("connects a proceed edge with an unlabeled arrow between the minted node ids", () => {
        const { diagram } = compileFlowGraph(
            makeGraph(
                [
                    makeNode("flow_start", DiagramNodeTypeEnum.FlowStart, { name: "Log out" }),
                    makeNode("done", DiagramNodeTypeEnum.FlowEnd),
                ],
                [makeEdge("flow_start", "done")],
            ),
        );

        expect(diagram).toBe(
            ["graph TD", 'n0[["Flow\nLog out"]]', 'n1[["End of the flow"]]', "n0 --> n1"].join(
                "\n",
            ),
        );
    });

    describe("edge labels", () => {
        it("labels a policy-passed edge with the passing verdict", () => {
            expect(compileEdge(DiagramEdgeTypeEnum.PolicyPassed)).toBe("n0 --Policy passed--> n1");
        });

        it("labels a policy-denied edge with the denying verdict", () => {
            expect(compileEdge(DiagramEdgeTypeEnum.PolicyDenied)).toBe("n0 --Policy denied--> n1");
        });

        it("labels a requirement-fulfilled edge with the fulfilled requirement", () => {
            expect(compileEdge(DiagramEdgeTypeEnum.RequirementFulfilled)).toBe(
                "n0 --Requirement met--> n1",
            );
        });

        it("labels a requirement-unfulfilled edge with the unmet requirement", () => {
            expect(compileEdge(DiagramEdgeTypeEnum.RequirementUnfulfilled)).toBe(
                "n0 --Denied--> n1",
            );
        });

        it("labels a binding edge with the binding order of the node it points at", () => {
            expect(compileEdge(DiagramEdgeTypeEnum.Binding, { bindingOrder: 3 })).toBe(
                "n0 --Binding 3--> n1",
            );
        });
    });

    it("leaves a binding edge unlabeled when its target carries no binding order", () => {
        expect(compileEdge(DiagramEdgeTypeEnum.Binding)).toBe("n0 --> n1");
    });

    it("escapes double quotes in a label so they cannot close the mermaid string", () => {
        const { diagram } = compileFlowGraph(
            makeGraph(
                [
                    makeNode("stage_0", DiagramNodeTypeEnum.Stage, {
                        name: 'the "special" stage',
                        verboseName: "Prompt Stage",
                    }),
                ],
                [],
            ),
        );

        expect(diagram).toBe(
            ["graph TD", 'n0(["Stage (Prompt Stage)\nthe #quot;special#quot; stage"])'].join("\n"),
        );
    });

    it("returns each node keyed by the mermaid id it was assigned", () => {
        const stage = makeNode("stage_0", DiagramNodeTypeEnum.Stage, { pk: "stage-pk" });
        const { nodes } = compileFlowGraph(
            makeGraph([makeNode("flow_start", DiagramNodeTypeEnum.FlowStart), stage], []),
        );

        expect(nodes.get("n1")).toBe(stage);
    });

    // The `initial-setup` flow as the server sends it: an authentication requirement,
    // a pre-flow policy, and a gated stage that skips forward when its policy denies.
    it("compiles a complete flow with a requirement, a flow policy, and a gated stage", () => {
        const graph = makeGraph(
            [
                makeNode("flow_auth_requirement", DiagramNodeTypeEnum.AuthenticationRequirement, {
                    name: "require_superuser",
                }),
                makeNode("flow_pre", DiagramNodeTypeEnum.PreFlowPolicies),
                makeNode("flow_policy_0", DiagramNodeTypeEnum.Policy, {
                    name: "default-oobe-password-usable",
                    verboseName: "Expression Policy",
                    bindingOrder: 0,
                }),
                makeNode("flow_start", DiagramNodeTypeEnum.FlowStart, {
                    name: "default-oobe-setup",
                }),
                makeNode("stage_0", DiagramNodeTypeEnum.Stage, {
                    name: "stage-default-oobe-password",
                    verboseName: "Prompt Stage",
                    bindingOrder: 10,
                }),
                makeNode("stage_1_policy_0", DiagramNodeTypeEnum.Policy, {
                    name: "default-oobe-prefill-user",
                    verboseName: "Expression Policy",
                    bindingOrder: 0,
                }),
                makeNode("stage_1", DiagramNodeTypeEnum.Stage, {
                    name: "default-password-change-write",
                    verboseName: "User Write Stage",
                    bindingOrder: 20,
                }),
                makeNode("stage_2", DiagramNodeTypeEnum.Stage, {
                    name: "default-authentication-login",
                    verboseName: "User Login Stage",
                    bindingOrder: 100,
                }),
                makeNode("done", DiagramNodeTypeEnum.FlowEnd),
            ],
            [
                makeEdge(
                    "flow_auth_requirement",
                    "done",
                    DiagramEdgeTypeEnum.RequirementUnfulfilled,
                ),
                makeEdge(
                    "flow_auth_requirement",
                    "flow_start",
                    DiagramEdgeTypeEnum.RequirementFulfilled,
                ),
                makeEdge("flow_pre", "flow_policy_0", DiagramEdgeTypeEnum.Binding),
                makeEdge("flow_policy_0", "done", DiagramEdgeTypeEnum.PolicyDenied),
                makeEdge("flow_policy_0", "flow_start"),
                makeEdge("flow_start", "stage_0"),
                makeEdge("stage_0", "stage_1_policy_0"),
                makeEdge("stage_1_policy_0", "stage_1", DiagramEdgeTypeEnum.PolicyPassed),
                makeEdge("stage_1", "stage_2"),
                makeEdge("stage_1_policy_0", "stage_2", DiagramEdgeTypeEnum.PolicyDenied),
                makeEdge("stage_2", "done"),
            ],
        );

        const { diagram } = compileFlowGraph(graph);

        expect(diagram).toBe(
            [
                "graph TD",
                'n0["Flow authentication requirement\nrequire_superuser"]',
                'n1[["Pre-flow policies"]]',
                'n2{{"Policy (Expression Policy)\ndefault-oobe-password-usable"}}',
                'n3[["Flow\ndefault-oobe-setup"]]',
                'n4(["Stage (Prompt Stage)\nstage-default-oobe-password"])',
                'n5{{"Policy (Expression Policy)\ndefault-oobe-prefill-user"}}',
                'n6(["Stage (User Write Stage)\ndefault-password-change-write"])',
                'n7(["Stage (User Login Stage)\ndefault-authentication-login"])',
                'n8[["End of the flow"]]',
                "n0 --Denied--> n8",
                "n0 --Requirement met--> n3",
                "n1 --> n2",
                "n2 --Policy denied--> n8",
                "n2 --> n3",
                "n3 --> n4",
                "n4 --> n5",
                "n5 --Policy passed--> n6",
                "n6 --> n7",
                "n5 --Policy denied--> n7",
                "n7 --> n8",
            ].join("\n"),
        );
    });

    it("drops an edge that names a node the graph never declared", () => {
        const { diagram } = compileFlowGraph(
            makeGraph(
                [makeNode("flow_start", DiagramNodeTypeEnum.FlowStart, { name: "Log out" })],
                [makeEdge("flow_start", "a stage that isn't here")],
            ),
        );

        expect(diagram).toBe(["graph TD", 'n0[["Flow\nLog out"]]'].join("\n"));
    });
});

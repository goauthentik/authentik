import {
    assignErrors,
    collectNodePaths,
    describe as describeNode,
    errorOwner,
    factsForTarget,
    operandType,
    pluckConditionErrors,
    unavailableVariables,
    variableType,
} from "#admin/policies/conditional/utils";

import {
    ConditionCatalog,
    ConditionNode,
    ConditionOperandShapeEnum,
    ConditionParamKindEnum,
    ConditionTypeKindEnum,
} from "@goauthentik/api";

import { describe, expect, it } from "vitest";

const catalog: ConditionCatalog = {
    facts: [],
    targets: [
        { model: "authentik_flows.flow", verboseName: "Flow", facts: ["user", "flow_plan"] },
        {
            model: "authentik_events.notificationrule",
            verboseName: "Rule",
            facts: ["user", "event"],
        },
    ],
    variables: [
        {
            key: "user.email",
            label: "Email",
            description: "",
            type: { kind: ConditionTypeKindEnum.String, choices: [], item: null },
            requires: ["user"],
            param: ConditionParamKindEnum.None,
            app: "authentik_core",
            appVerboseName: "Core",
        },
        {
            key: "user.groups",
            label: "Groups",
            description: "",
            type: {
                kind: ConditionTypeKindEnum.List,
                choices: [],
                item: {
                    kind: ConditionTypeKindEnum.Model,
                    model: "authentik_core.group",
                    choices: [],
                },
            },
            requires: ["user"],
            param: ConditionParamKindEnum.None,
            app: "authentik_core",
            appVerboseName: "Core",
        },
        {
            key: "user.attributes",
            label: "Attribute",
            description: "",
            type: { kind: ConditionTypeKindEnum.Any, choices: [], item: null },
            requires: ["user"],
            param: ConditionParamKindEnum.Path,
            app: "authentik_core",
            appVerboseName: "Core",
        },
        {
            key: "event.action",
            label: "Event action",
            description: "",
            type: { kind: ConditionTypeKindEnum.Enum, choices: [], item: null },
            requires: ["event"],
            param: ConditionParamKindEnum.None,
            app: "authentik_events",
            appVerboseName: "Events",
        },
    ],
    operators: [
        {
            name: "eq",
            label: "equals",
            kinds: [ConditionTypeKindEnum.String, ConditionTypeKindEnum.Enum],
            operand: ConditionOperandShapeEnum.Same,
        },
        {
            name: "in",
            label: "is one of",
            kinds: [ConditionTypeKindEnum.String],
            operand: ConditionOperandShapeEnum.ListOfSame,
        },
        {
            name: "has_item",
            label: "contains item",
            kinds: [ConditionTypeKindEnum.List],
            operand: ConditionOperandShapeEnum.Item,
        },
        {
            name: "is_set",
            label: "is set",
            kinds: [ConditionTypeKindEnum.String],
            operand: ConditionOperandShapeEnum.None,
        },
    ],
};

const op = (name: string) => catalog.operators.find((o) => o.name === name);

describe("variableType", () => {
    it("returns the declared type", () => {
        expect(variableType(catalog, { key: "user.email" })?.kind).toBe("string");
    });

    it("uses the cast type for variables without a fixed type", () => {
        expect(variableType(catalog, { key: "user.attributes", param: "foo" })?.kind).toBe("any");

        expect(
            variableType(catalog, { key: "user.attributes", param: "foo", cast: "number" })?.kind,
        ).toBe("number");
    });

    it("returns null for unknown variables", () => {
        expect(variableType(catalog, { key: "nope" })).toBeNull();
    });
});

describe("operandType", () => {
    const email = variableType(catalog, { key: "user.email" });
    const groups = variableType(catalog, { key: "user.groups" });

    it("derives the operand type from the operator shape", () => {
        expect(operandType(op("eq"), email)?.kind).toBe("string");
        expect(operandType(op("in"), email)).toEqual({ kind: "list", item: email });
        expect(operandType(op("has_item"), groups)?.model).toBe("authentik_core.group");
    });

    it("returns null for operators without operand", () => {
        expect(operandType(op("is_set"), email)).toBeNull();
    });
});

describe("unavailableVariables", () => {
    const tree: ConditionNode = {
        type: "group",
        op: "all",
        children: [
            { type: "condition", variable: { key: "user.email" }, operator: "is_set" },
            {
                type: "not",
                child: { type: "condition", variable: { key: "event.action" }, operator: "is_set" },
            },
        ],
    };

    it("lists variables not available for a target", () => {
        const facts = factsForTarget(catalog, "authentik_flows.flow");
        expect(unavailableVariables(catalog, tree, facts)).toEqual(["event.action"]);
    });

    it("allows everything without a target", () => {
        expect(unavailableVariables(catalog, tree, factsForTarget(catalog, null))).toEqual([]);
    });
});

describe("describe", () => {
    it("renders a readable summary", () => {
        const tree: ConditionNode = {
            type: "group",
            op: "any",
            children: [
                {
                    type: "condition",
                    variable: { key: "user.email" },
                    operator: "in",
                    value: { type: "literal", value: ["a", "b"] },
                },
                {
                    type: "not",
                    child: {
                        type: "condition",
                        variable: { key: "user.attributes", param: "dept", cast: "string" },
                        operator: "eq",
                        value: { type: "variable", variable: { key: "user.email" } },
                    },
                },
            ],
        };

        expect(describeNode(catalog, tree)).toBe(
            '(Email is one of ["a", "b"] OR NOT Attribute "dept" equals Email)',
        );
    });
});

describe("validation errors", () => {
    const negated: ConditionNode = {
        type: "condition",
        variable: { key: "user.email" },
        operator: "is_set",
    };

    const tree: ConditionNode = {
        type: "group",
        op: "all",
        children: [
            { type: "condition", variable: { key: "user.email" }, operator: "is_set" },
            { type: "not", child: negated },
        ],
    };

    it("computes node paths like the API", () => {
        const paths = collectNodePaths(tree);

        expect([...paths.values()]).toEqual([
            "root",
            "root.children.0",
            "root.children.1",
            "root.children.1.child",
        ]);

        expect(paths.get(negated)).toBe("root.children.1.child");
    });

    it("assigns errors to the deepest matching node", () => {
        const paths = [...collectNodePaths(tree).values()];

        expect(errorOwner("root.children.1.child.operator", paths)).toBe("root.children.1.child");
        expect(errorOwner("root.children.10.operator", paths)).toBe("root");
        expect(errorOwner("version", paths)).toBe("");
    });

    it("groups messages and prefixes fields", () => {
        const paths = collectNodePaths(tree).values();

        const errors = assignErrors(
            {
                "root.children.0": ["Group must contain at least one item"],
                "root.children.1.child.value.variable.key": ["Field required"],
                "version": ["Input should be less than or equal to 1"],
            },
            paths,
        );

        expect(errors.get("root.children.0")).toEqual(["Group must contain at least one item"]);
        expect(errors.get("root.children.1.child")).toEqual(["value.variable.key: Field required"]);
        expect(errors.get("")).toEqual(["version: Input should be less than or equal to 1"]);
    });

    it("plucks errors from the API response", () => {
        expect(
            pluckConditionErrors({
                conditions: { detail: "1 error", nodes: { "root.children.0.operator": ["x"] } },
            }),
        ).toEqual({ "root.children.0.operator": ["x"] });

        expect(pluckConditionErrors({ name: ["required"] })).toEqual({});
        expect(pluckConditionErrors(null)).toEqual({});
    });
});

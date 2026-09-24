import {
    assignErrors,
    collectPaths,
    describeAction,
    filterPickerOptions,
    operatorChoices,
    pickerOptions,
    removeNotNodes,
    collectNodePaths,
    describe as describeNode,
    errorOwner,
    factsForScenario,
    operandType,
    pluckConditionErrors,
    unavailableVariables,
    variableType,
} from "#admin/policies/conditional/utils";

import {
    ConditionCatalog,
    ConditionNode,
    PolicyAction,
    ConditionOperandShapeEnum,
    ConditionParamKindEnum,
    ConditionTypeKindEnum,
} from "@goauthentik/api";

import { describe, expect, it } from "vitest";

const catalog: ConditionCatalog = {
    facts: [],
    scenarios: [
        {
            key: "flow_execution",
            label: "Flow execution",
            description: "",
            facts: ["user", "flow_plan"],
        },
        {
            key: "notification_rule",
            label: "Notification rule",
            description: "",
            facts: ["user", "event"],
        },
    ],
    variables: [
        {
            key: "device.facts",
            label: "Device fact",
            description: "",
            type: { kind: ConditionTypeKindEnum.Any, choices: [], item: null },
            requires: ["device"],
            param: ConditionParamKindEnum.Path,
            params: [
                {
                    key: "hardware.manufacturer",
                    label: "Hardware › Manufacturer",
                    type: { kind: ConditionTypeKindEnum.String, choices: [], item: null },
                },
            ],
            app: "authentik_endpoints",
            appVerboseName: "Endpoints",
        },
        {
            key: "user.email",
            label: "Email",
            description: "",
            type: { kind: ConditionTypeKindEnum.String, choices: [], item: null },
            requires: ["user"],
            param: ConditionParamKindEnum.None,
            params: [],
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
            params: [],
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
            params: [],
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
            params: [],
            app: "authentik_events",
            appVerboseName: "Events",
        },
    ],
    setters: [],
    operators: [
        {
            name: "contains",
            label: "contains",
            kinds: [ConditionTypeKindEnum.String],
            operand: ConditionOperandShapeEnum.Same,
            negatedLabel: "does not contain",
        },
        {
            name: "eq",
            label: "equals",
            kinds: [ConditionTypeKindEnum.String, ConditionTypeKindEnum.Enum],
            operand: ConditionOperandShapeEnum.Same,
            negatedLabel: null,
        },
        {
            name: "in",
            label: "is one of",
            kinds: [ConditionTypeKindEnum.String],
            operand: ConditionOperandShapeEnum.ListOfSame,
            negatedLabel: null,
        },
        {
            name: "has_item",
            label: "contains item",
            kinds: [ConditionTypeKindEnum.List],
            operand: ConditionOperandShapeEnum.Item,
            negatedLabel: null,
        },
        {
            name: "is_set",
            label: "is set",
            kinds: [ConditionTypeKindEnum.String],
            operand: ConditionOperandShapeEnum.None,
            negatedLabel: null,
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
            { type: "compare", variable: { key: "user.email" }, operator: "is_set" },
            {
                type: "not",
                child: { type: "compare", variable: { key: "event.action" }, operator: "is_set" },
            },
        ],
    };

    it("lists variables not available for a target", () => {
        const facts = factsForScenario(catalog, "flow_execution");
        expect(unavailableVariables(catalog, tree, facts)).toEqual(["event.action"]);
    });

    it("allows everything without a target", () => {
        expect(unavailableVariables(catalog, tree, factsForScenario(catalog, null))).toEqual([]);
    });
});

describe("describe", () => {
    it("renders a readable summary", () => {
        const tree: ConditionNode = {
            type: "group",
            op: "any",
            children: [
                {
                    type: "compare",
                    variable: { key: "user.email" },
                    operator: "in",
                    value: { type: "literal", value: ["a", "b"] },
                },
                {
                    type: "not",
                    child: {
                        type: "compare",
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
        type: "compare",
        variable: { key: "user.email" },
        operator: "is_set",
    };

    const tree: ConditionNode = {
        type: "group",
        op: "all",
        children: [
            { type: "compare", variable: { key: "user.email" }, operator: "is_set" },
            { type: "not", child: negated },
        ],
    };

    it("computes node paths like the API", () => {
        const action: PolicyAction = { type: "condition", condition: tree };
        const paths = collectPaths([action]);

        expect([...paths.values()]).toEqual([
            "actions.0",
            "actions.0.condition",
            "actions.0.condition.children.0",
            "actions.0.condition.children.1",
            "actions.0.condition.children.1.child",
        ]);

        expect(paths.get(negated)).toBe("actions.0.condition.children.1.child");
    });

    it("assigns errors to the deepest matching node", () => {
        const paths = [...collectNodePaths(tree, "root").values()];

        expect(errorOwner("root.children.1.child.operator", paths)).toBe("root.children.1.child");
        expect(errorOwner("root.children.10.operator", paths)).toBe("root");
        expect(errorOwner("version", paths)).toBe("");
    });

    it("groups messages and prefixes fields", () => {
        const paths = collectNodePaths(tree, "root").values();

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
                actions: { detail: "1 error", nodes: { "root.children.0.operator": ["x"] } },
            }),
        ).toEqual({ "root.children.0.operator": ["x"] });

        expect(pluckConditionErrors({ name: ["required"] })).toEqual({});
        expect(pluckConditionErrors(null)).toEqual({});
    });
});

describe("variable picker", () => {
    it("offers well-defined parameters as separate entries", () => {
        const options = pickerOptions(catalog, null);
        const device = options.filter((option) => option.key === "device.facts");

        expect(device.map((option) => [option.label, option.param])).toEqual([
            ["Hardware › Manufacturer", "hardware.manufacturer"],
            ["Device fact (custom path)", null],
        ]);

        expect(device[0].type.kind).toBe("string");
        expect(device[0].category).toBe("Device");
    });

    it("types known parameters without a cast", () => {
        expect(
            variableType(catalog, { key: "device.facts", param: "hardware.manufacturer" })?.kind,
        ).toBe("string");

        expect(variableType(catalog, { key: "device.facts", param: "other" })?.kind).toBe("any");
    });

    it("marks values that aren't available", () => {
        const facts = factsForScenario(catalog, "flow_execution");
        const device = pickerOptions(catalog, facts).find((o) => o.key === "device.facts");

        expect(device?.available).toBe(false);
    });

    it("filters by category, label and key", () => {
        const options = pickerOptions(catalog, null);

        expect(filterPickerOptions(options, "device manuf").map((o) => o.param)).toEqual([
            "hardware.manufacturer",
        ]);

        expect(filterPickerOptions(options, "user.email").map((o) => o.key)).toEqual([
            "user.email",
        ]);
    });
});

describe("operators", () => {
    it("lists negated forms after the operator", () => {
        const email = variableType(catalog, { key: "user.email" });

        expect(operatorChoices(catalog, email).map((choice) => choice.label)).toEqual([
            "contains",
            "does not contain",
            "equals",
            "is one of",
            "is set",
        ]);
    });

    it("replaces not nodes", () => {
        const tree: ConditionNode = {
            type: "group",
            op: "all",
            children: [
                {
                    type: "not",
                    child: {
                        type: "compare",
                        variable: { key: "user.email" },
                        operator: "contains",
                    },
                },
                {
                    type: "not",
                    child: { type: "compare", variable: { key: "user.email" }, operator: "eq" },
                },
                {
                    type: "not",
                    child: { type: "group", op: "any", children: [] },
                },
                {
                    type: "not",
                    child: { type: "policy", policy: "foo" },
                },
            ],
        };

        const result = removeNotNodes(catalog, tree);

        expect(result).toEqual({
            type: "group",
            op: "all",
            children: [
                {
                    type: "compare",
                    variable: { key: "user.email" },
                    operator: "contains",
                    options: { negate: true },
                },
                { type: "compare", variable: { key: "user.email" }, operator: "ne" },
                { type: "group", op: "none", children: [] },
                { type: "group", op: "none", children: [{ type: "policy", policy: "foo" }] },
            ],
        });
    });
});

describe("actions", () => {
    it("computes paths of nested actions like the API", () => {
        const stop: PolicyAction = { type: "stop", result: "fail" };

        const paths = collectPaths([
            {
                type: "if",
                condition: { type: "compare", variable: { key: "user.email" }, operator: "is_set" },
                thenActions: [],
                elseActions: [stop],
            },
        ]);

        expect(paths.get(stop)).toBe("actions.0.else_actions.0");
        expect([...paths.values()]).toContain("actions.0.condition");
    });

    it("describes actions", () => {
        expect(
            describeAction(catalog, {
                type: "set",
                target: { key: "plan.context", param: "foo" },
                value: { type: "literal", value: "bar" },
            }),
        ).toBe('Set plan.context "foo" to "bar"');

        expect(describeAction(catalog, { type: "stop", result: "fail", message: "No" })).toBe(
            'Stop and fail: "No"',
        );
    });
});

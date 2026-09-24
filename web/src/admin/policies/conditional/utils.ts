/**
 * Pure helpers for building condition trees of conditional policies.
 *
 * The type rules here mirror `authentik/policies/conditional/operators.py`; the server
 * validates the tree again on save.
 */

import {
    ConditionCastKind,
    ConditionCatalog,
    ConditionComparisonNode,
    ConditionItemType,
    ConditionNode,
    ConditionOperandShapeEnum,
    ConditionOperator,
    ConditionTarget,
    ConditionTree,
    ConditionTypeKindEnum,
    ConditionVariable,
    ConditionVariableRef,
} from "@goauthentik/api";

export const SCHEMA_VERSION = 1;

/**
 * A resolved value type. Unlike the API's `ConditionValueType`, the item type of a list may
 * itself be a list (for example the operand of `in` for a list of values).
 */
export interface ValueType {
    kind: ConditionTypeKindEnum;
    model?: string | null;
    choices?: ConditionItemType["choices"];
    item?: ValueType | null;
}

export const CAST_KINDS: ConditionCastKind[] = Object.values(ConditionCastKind).filter(
    (kind) => kind !== ConditionCastKind.UnknownDefaultOpenApi,
);

export function emptyTree(): ConditionTree {
    return {
        version: SCHEMA_VERSION,
        root: { type: "group", op: "all", children: [] },
    };
}

export function newCondition(): ConditionComparisonNode & { type: "condition" } {
    return {
        type: "condition",
        variable: { key: "" },
        operator: "is_set",
        value: null,
    };
}

export function findVariable(
    catalog: ConditionCatalog | undefined,
    key: string,
): ConditionVariable | undefined {
    return catalog?.variables.find((variable) => variable.key === key);
}

/**
 * Type of a variable reference, after an optional cast. Variables without a fixed type
 * that aren't cast have the type `any`.
 */
export function variableType(
    catalog: ConditionCatalog | undefined,
    ref: ConditionVariableRef,
): ValueType | null {
    const variable = findVariable(catalog, ref.key);

    if (!variable) return null;

    if (variable.type.kind === ConditionTypeKindEnum.Any) {
        // Without a cast, only the presence of the value can be checked
        if (!ref.cast) return { kind: ConditionTypeKindEnum.Any };

        return { kind: ref.cast as ConditionTypeKindEnum };
    }

    return variable.type;
}

export function operatorsFor(
    catalog: ConditionCatalog | undefined,
    type: ValueType | null,
): ConditionOperator[] {
    if (!catalog || !type) return [];

    return catalog.operators.filter((operator) => operator.kinds.includes(type.kind));
}

function listOf(item: ValueType): ValueType {
    return { kind: ConditionTypeKindEnum.List, item };
}

/**
 * Type of the value an operator expects for a variable of type `type`, or `null` if the
 * operator doesn't take a value.
 */
export function operandType(
    operator: ConditionOperator | undefined,
    type: ValueType | null,
): ValueType | null {
    if (!operator || !type) return null;
    const any: ValueType = { kind: ConditionTypeKindEnum.Any };

    switch (operator.operand) {
        case ConditionOperandShapeEnum.Same:
            return type;
        case ConditionOperandShapeEnum.ListOfSame:
        case ConditionOperandShapeEnum.Range:
            return listOf(type);
        case ConditionOperandShapeEnum.Item:
            return type.item ?? any;
        case ConditionOperandShapeEnum.ListOfItem:
            return listOf(type.item ?? any);
        case ConditionOperandShapeEnum.Number:
            return { kind: ConditionTypeKindEnum.Number };
        case ConditionOperandShapeEnum.Duration:
            return { kind: ConditionTypeKindEnum.Duration };
        case ConditionOperandShapeEnum.Regex:
            return { kind: ConditionTypeKindEnum.String };
        case ConditionOperandShapeEnum.CidrList:
            return listOf({ kind: ConditionTypeKindEnum.Cidr });
        default:
            return null;
    }
}

export function isTextual(type: ValueType | null): boolean {
    if (!type) return false;

    if (type.kind === ConditionTypeKindEnum.List) return isTextual(type.item ?? null);

    return type.kind === ConditionTypeKindEnum.String || type.kind === ConditionTypeKindEnum.Enum;
}

/**
 * Facts available for the selected target, or `null` when no target is selected.
 */
export function factsForTarget(
    catalog: ConditionCatalog | undefined,
    target: string | null,
): Set<string> | null {
    if (!catalog || !target) return null;
    const found = catalog.targets.find((t: ConditionTarget) => t.model === target);

    return found ? new Set(found.facts) : null;
}

export function isAvailable(variable: ConditionVariable, facts: Set<string> | null): boolean {
    if (!facts) return true;

    return variable.requires.some((fact) => facts.has(fact));
}

/**
 * Keys of all variables used in a tree which are not available for `facts`.
 */
export function unavailableVariables(
    catalog: ConditionCatalog | undefined,
    node: ConditionNode,
    facts: Set<string> | null,
): string[] {
    if (!facts || !catalog) return [];
    const result = new Set<string>();

    const check = (ref?: ConditionVariableRef | null) => {
        if (!ref) return;
        const variable = findVariable(catalog, ref.key);

        if (variable && !isAvailable(variable, facts)) result.add(variable.key);
    };

    const walk = (current: ConditionNode) => {
        switch (current.type) {
            case "group":
                current.children.forEach(walk);
                break;
            case "not":
                walk(current.child);
                break;
            case "condition":
                check(current.variable);
                if (current.value?.type === "variable") check(current.value.variable);
                break;
        }
    };

    walk(node);

    return [...result].sort();
}

function describeRef(catalog: ConditionCatalog | undefined, ref: ConditionVariableRef) {
    const label = findVariable(catalog, ref.key)?.label ?? ref.key;

    return ref.param ? `${label} "${ref.param}"` : label;
}

function describeValue(value: unknown): string {
    if (Array.isArray(value)) return `[${value.map(describeValue).join(", ")}]`;

    if (typeof value === "string") return `"${value}"`;

    return String(value);
}

/**
 * Human readable, single line description of a node.
 */
export function describe(catalog: ConditionCatalog | undefined, node: ConditionNode): string {
    switch (node.type) {
        case "group": {
            if (node.children.length === 0) return "()";
            const joiner = node.op === "all" ? " AND " : " OR ";
            const inner = node.children.map((child) => describe(catalog, child)).join(joiner);

            return node.children.length > 1 ? `(${inner})` : inner;
        }
        case "not":
            return `NOT ${describe(catalog, node.child)}`;
        case "policy":
            return `policy(${node.policy})`;
        case "condition": {
            const operator =
                catalog?.operators.find((op) => op.name === node.operator)?.label ?? node.operator;

            let text = `${describeRef(catalog, node.variable)} ${operator}`;

            if (node.value?.type === "literal") {
                text += ` ${describeValue(node.value.value)}`;
            } else if (node.value?.type === "variable") {
                text += ` ${describeRef(catalog, node.value.variable)}`;
            }

            return text;
        }
        default:
            return "";
    }
}

//#region Validation errors

/**
 * Validation errors of a condition tree, keyed by the path of the node and field they belong
 * to, for example `root.children.1.operator`.
 */
export type ConditionErrors = Record<string, string[]>;

/**
 * Paths of all nodes in a tree, in the same format the API uses for validation errors.
 */
export function collectNodePaths(
    node: ConditionNode,
    path = "root",
    paths = new Map<ConditionNode, string>(),
): Map<ConditionNode, string> {
    paths.set(node, path);

    if (node.type === "group") {
        node.children.forEach((child, index) =>
            collectNodePaths(child, `${path}.children.${index}`, paths),
        );
    } else if (node.type === "not") {
        collectNodePaths(node.child, `${path}.child`, paths);
    }

    return paths;
}

/**
 * Path of the node an error belongs to: the deepest node whose path is a prefix of the error's
 * path. Empty if the error doesn't belong to any node.
 */
export function errorOwner(key: string, nodePaths: Iterable<string>): string {
    let owner = "";

    for (const path of nodePaths) {
        if ((key === path || key.startsWith(`${path}.`)) && path.length > owner.length) {
            owner = path;
        }
    }

    return owner;
}

/**
 * Group errors by the node they belong to. Messages for a field of a node are prefixed with the
 * field, errors which don't belong to any node are grouped under an empty path.
 */
export function assignErrors(
    errors: ConditionErrors,
    nodePaths: Iterable<string>,
): Map<string, string[]> {
    const paths = [...nodePaths];
    const result = new Map<string, string[]>();

    for (const [key, messages] of Object.entries(errors)) {
        const owner = errorOwner(key, paths);
        const field = owner ? key.slice(owner.length + 1) : key;
        const existing = result.get(owner) ?? [];

        existing.push(...messages.map((message) => (field ? `${field}: ${message}` : message)));
        result.set(owner, existing);
    }

    return result;
}

//#endregion

/**
 * Pluck the validation errors of the conditions from an API error response body, which has
 * the shape `{"conditions": {"detail": "...", "nodes": {"<path>": ["<message>"]}}}`.
 */
export function pluckConditionErrors(body: unknown): ConditionErrors {
    if (!body || typeof body !== "object" || !("conditions" in body)) return {};

    const { conditions } = body;

    if (!conditions || typeof conditions !== "object" || !("nodes" in conditions)) return {};

    const { nodes } = conditions;

    if (!nodes || typeof nodes !== "object") return {};

    return Object.fromEntries(
        Object.entries(nodes).map(([path, messages]) => [
            path,
            (Array.isArray(messages) ? messages : [messages]).map(String),
        ]),
    );
}

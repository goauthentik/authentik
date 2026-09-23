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
 * Type of a variable reference, after an optional cast.
 */
export function variableType(
    catalog: ConditionCatalog | undefined,
    ref: ConditionVariableRef,
): ValueType | null {
    const variable = findVariable(catalog, ref.key);
    if (!variable) return null;
    if (variable.type.kind === ConditionTypeKindEnum.Any) {
        if (!ref.cast) return null;
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

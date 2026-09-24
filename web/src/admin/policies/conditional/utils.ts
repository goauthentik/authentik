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
    PolicyAction,
    PolicyActions,
    ConditionTypeKindEnum,
    ConditionVariable,
    ConditionVariableRef,
} from "@goauthentik/api";

export const SCHEMA_VERSION = 2;

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

export function emptyActions(): PolicyActions {
    return { version: SCHEMA_VERSION, actions: [] };
}

export type CompareNode = ConditionComparisonNode & { type: "compare" };

export function newCondition(): CompareNode {
    return {
        type: "compare",
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

    const known = variable.params.find((param) => param.key === ref.param);

    if (known && !ref.cast) return known.type;

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
            case "compare":
                check(current.variable);
                if (current.value?.type === "variable") check(current.value.variable);
                break;
        }
    };

    walk(node);

    return [...result].sort();
}

function describeRef(catalog: ConditionCatalog | undefined, ref: ConditionVariableRef) {
    const variable = findVariable(catalog, ref.key);
    const label = variable?.label ?? ref.key;
    const known = variable?.params.find((param) => param.key === ref.param);

    if (known) return `${label} ${known.label}`;

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

            if (node.op === "none") return `NOT (${inner})`;

            return node.children.length > 1 ? `(${inner})` : inner;
        }
        case "not":
            return `NOT ${describe(catalog, node.child)}`;
        case "policy":
            return `policy(${node.policy})`;
        case "compare": {
            const found = catalog?.operators.find((op) => op.name === node.operator);

            const operator =
                (node.options?.negate ? found?.negatedLabel : found?.label) ?? node.operator;

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
    path: string,
    paths = new Map<object, string>(),
): Map<object, string> {
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
 * Paths of all actions and conditions, in the same format the API uses for validation errors.
 */
export function collectPaths(
    actions: PolicyAction[],
    path = "actions",
    paths = new Map<object, string>(),
): Map<object, string> {
    actions.forEach((action, index) => {
        const actionPath = `${path}.${index}`;

        paths.set(action, actionPath);

        if (action.type === "condition" || action.type === "if") {
            collectNodePaths(action.condition, `${actionPath}.condition`, paths);
        }

        if (action.type === "if") {
            collectPaths(action.thenActions ?? [], `${actionPath}.then_actions`, paths);
            collectPaths(action.elseActions ?? [], `${actionPath}.else_actions`, paths);
        }
    });

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
 * the shape `{"actions": {"detail": "...", "nodes": {"<path>": ["<message>"]}}}`.
 */
export function pluckConditionErrors(body: unknown): ConditionErrors {
    if (!body || typeof body !== "object" || !("actions" in body)) return {};

    const { actions } = body;

    if (!actions || typeof actions !== "object" || !("nodes" in actions)) return {};

    const { nodes } = actions;

    if (!nodes || typeof nodes !== "object") return {};

    return Object.fromEntries(
        Object.entries(nodes).map(([path, messages]) => [
            path,
            (Array.isArray(messages) ? messages : [messages]).map(String),
        ]),
    );
}

//#region Picker

/**
 * Category a variable is shown under in the picker, based on the first segment of its key.
 */
export function variableCategory(variable: ConditionVariable): string {
    const prefix = variable.key.split(".")[0];

    switch (prefix) {
        case "user":
            return "User";
        case "request":
            return "Request";
        case "application":
            return "Application";
        case "flow":
        case "plan":
            return "Flow";
        case "prompt_data":
            return "Prompt";
        case "event":
            return "Event";
        case "device":
            return "Device";
        case "oauth":
            return "OAuth2";
        case "invitation":
            return "Invitation";
        default:
            return variable.appVerboseName || variable.app;
    }
}

/**
 * An entry of the variable picker: a variable, or a well-defined parameter of a variable.
 */
export interface PickerOption {
    id: string;
    key: string;
    param: string | null;
    category: string;
    label: string;
    description: string;
    type: ValueType;
    available: boolean;
}

export function pickerOptionId(ref: Pick<ConditionVariableRef, "key" | "param">): string {
    return `${ref.key}|${ref.param ?? ""}`;
}

/**
 * All entries of the variable picker. Variables with well-defined parameters (like device
 * facts) get an entry per parameter, next to the entry for a custom path.
 */
export function pickerOptions(
    catalog: ConditionCatalog | undefined,
    facts: Set<string> | null,
): PickerOption[] {
    if (!catalog) return [];

    return catalog.variables.flatMap((variable) => {
        const category = variableCategory(variable);
        const available = isAvailable(variable, facts);

        const options: PickerOption[] = variable.params.map((param) => ({
            id: pickerOptionId({ key: variable.key, param: param.key }),
            key: variable.key,
            param: param.key,
            category,
            label: param.label,
            description: variable.description,
            type: param.type,
            available,
        }));

        options.push({
            id: pickerOptionId({ key: variable.key, param: null }),
            key: variable.key,
            param: null,
            category,
            label:
                variable.params.length && variable.param !== "none"
                    ? `${variable.label} (custom path)`
                    : variable.label,
            description: variable.description,
            type: variable.type,
            available,
        });

        return options;
    });
}

/**
 * Filter picker entries by a search query, matching the label, category and key.
 */
export function filterPickerOptions(options: PickerOption[], query?: string): PickerOption[] {
    const terms = (query ?? "").toLowerCase().split(/\s+/).filter(Boolean);

    return options.filter((option) => {
        const haystack =
            `${option.category} ${option.label} ${option.key} ${option.param ?? ""}`.toLowerCase();

        return terms.every((term) => haystack.includes(term));
    });
}

//#endregion

//#region Operators

/**
 * An entry of the operator dropdown. Operators which can be negated get a second entry.
 */
export interface OperatorChoice {
    id: string;
    name: ConditionOperator["name"];
    negate: boolean;
    label: string;
}

export function operatorChoiceId(name: string, negate?: boolean): string {
    return negate ? `${name}:not` : name;
}

export function operatorChoices(
    catalog: ConditionCatalog | undefined,
    type: ValueType | null,
): OperatorChoice[] {
    return operatorsFor(catalog, type).flatMap((operator) => {
        const choices: OperatorChoice[] = [
            {
                id: operatorChoiceId(operator.name),
                name: operator.name,
                negate: false,
                label: operator.label,
            },
        ];

        if (operator.negatedLabel) {
            choices.push({
                id: operatorChoiceId(operator.name, true),
                name: operator.name,
                negate: true,
                label: operator.negatedLabel,
            });
        }

        return choices;
    });
}

/**
 * Operators which have an explicit opposite, used to remove `not` nodes.
 */
const OPPOSITE_OPERATORS: Record<string, ConditionOperator["name"]> = {
    eq: "ne",
    ne: "eq",
    in: "not_in",
    not_in: "in",
    is_set: "is_not_set",
    is_not_set: "is_set",
    is_true: "is_false",
    is_false: "is_true",
};

/**
 * Negate a single node without using a `not` node, if possible.
 */
function negate(catalog: ConditionCatalog, node: ConditionNode): ConditionNode {
    if (node.type === "compare") {
        const opposite = OPPOSITE_OPERATORS[node.operator];

        if (opposite && !node.options?.negate) {
            return { ...node, operator: opposite };
        }

        const operator = catalog.operators.find((op) => op.name === node.operator);

        if (operator?.negatedLabel) {
            return {
                ...node,
                options: { ...node.options, negate: !node.options?.negate },
            };
        }
    }

    if (node.type === "group" && node.op !== "all") {
        return { ...node, op: node.op === "any" ? "none" : "any" };
    }

    if (node.type === "not") return node.child;

    return { type: "group", op: "none", children: [node] };
}

/**
 * Replace `not` nodes, which the editor doesn't show, with equivalent nodes: negated
 * operators, or groups where none of the children may pass.
 */
export function removeNotNodes(catalog: ConditionCatalog, node: ConditionNode): ConditionNode {
    switch (node.type) {
        case "not":
            return negate(catalog, removeNotNodes(catalog, node.child));
        case "group":
            return {
                ...node,
                children: node.children.map((child) => removeNotNodes(catalog, child)),
            };
        default:
            return node;
    }
}

//#endregion

/**
 * Replace `not` nodes in all conditions of `actions`.
 */
export function removeNotNodesFromActions(
    catalog: ConditionCatalog,
    actions: PolicyAction[],
): PolicyAction[] {
    return actions.map((action) => {
        switch (action.type) {
            case "condition":
                return { ...action, condition: removeNotNodes(catalog, action.condition) };
            case "if":
                return {
                    ...action,
                    condition: removeNotNodes(catalog, action.condition),
                    thenActions: removeNotNodesFromActions(catalog, action.thenActions ?? []),
                    elseActions: removeNotNodesFromActions(catalog, action.elseActions ?? []),
                };
            default:
                return action;
        }
    });
}

//#region Actions

export function findSetter(catalog: ConditionCatalog | undefined, key: string) {
    return catalog?.setters.find((setter) => setter.key === key);
}

function describeOperand(
    catalog: ConditionCatalog | undefined,
    operand: ConditionComparisonNode["value"],
): string {
    if (operand?.type === "literal") return describeValue(operand.value);

    if (operand?.type === "variable") return describeRef(catalog, operand.variable);

    return "…";
}

/**
 * Human readable, single line description of an action.
 */
export function describeAction(
    catalog: ConditionCatalog | undefined,
    action: PolicyAction,
): string {
    switch (action.type) {
        case "condition":
            return describe(catalog, action.condition);
        case "if":
            return `If ${describe(catalog, action.condition)}`;
        case "set": {
            const setter = findSetter(catalog, action.target.key);
            const label = setter?.label ?? (action.target.key || "…");
            const target = action.target.param ? `${label} "${action.target.param}"` : label;

            return `Set ${target} to ${describeOperand(catalog, action.value)}`;
        }
        case "stop": {
            const result = action.result === "pass" ? "pass" : "fail";

            return action.message
                ? `Stop and ${result}: "${action.message}"`
                : `Stop and ${result}`;
        }
        default:
            return "";
    }
}

//#endregion

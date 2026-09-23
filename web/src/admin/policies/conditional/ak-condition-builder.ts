import "#elements/Spinner";
import "#elements/forms/SearchSelect/index";

import { aki } from "#common/api/client";

import { AKControlElement } from "#elements/ControlElement";

import {
    CAST_KINDS,
    describe,
    emptyTree,
    factsForTarget,
    findVariable,
    isAvailable,
    isTextual,
    newCondition,
    operandType,
    operatorsFor,
    unavailableVariables,
    ValueType,
    variableType,
} from "#admin/policies/conditional/utils";

import {
    Application,
    ConditionCatalog,
    ConditionComparisonNodeRequest,
    ConditionGroupNodeRequest,
    ConditionNodeRequest,
    ConditionOperatorEnum,
    ConditionParamKindEnum,
    ConditionTreeRequest,
    ConditionTypeKindEnum,
    ConditionVariable,
    ConditionVariableRefRequest,
    CoreApi,
    Group,
    PoliciesApi,
    Policy,
    Source,
    SourcesApi,
    User,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, html, nothing, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLabel from "@patternfly/patternfly/components/Label/label.css";

type Condition = ConditionComparisonNodeRequest & { type: "condition" };
type GroupNode = ConditionGroupNodeRequest & { type: "group" };

interface ModelLookup<T> {
    fetch: (search?: string) => Promise<T[]>;
    render: (obj: T) => string;
    value: (obj: T | null) => string | undefined;
}

type AnyLookup = ModelLookup<Application | Group | Source | User>;

/**
 * Lookups for model references, keyed by model label. Models not listed here are entered by
 * primary key.
 */
const MODEL_LOOKUPS: Record<string, AnyLookup> = {
    "authentik_core.group": {
        fetch: async (search) =>
            (await aki(CoreApi).coreGroupsList({ search, ordering: "name", includeUsers: false }))
                .results,
        render: (obj) => (obj as Group).name,
        value: (obj) => (obj as Group | null)?.pk,
    },
    "authentik_core.user": {
        fetch: async (search) =>
            (await aki(CoreApi).coreUsersList({ search, ordering: "username" })).results,
        render: (obj) => (obj as User).username,
        value: (obj) => (obj ? String((obj as User).pk) : undefined),
    },
    "authentik_core.application": {
        fetch: async (search) =>
            (await aki(CoreApi).coreApplicationsList({ search, ordering: "name" })).results,
        render: (obj) => (obj as Application).name,
        value: (obj) => (obj as Application | null)?.pk,
    },
    "authentik_core.source": {
        fetch: async (search) =>
            (await aki(SourcesApi).sourcesAllList({ search, ordering: "name" })).results,
        render: (obj) => (obj as Source).name,
        value: (obj) => (obj as Source | null)?.pk,
    },
};

function toLocalDatetime(value: unknown): string {
    if (typeof value !== "string" || !value) return "";
    const date = new Date(value);
    if (isNaN(date.getTime())) return "";
    const offset = date.getTimezoneOffset() * 60_000;
    return new Date(date.getTime() - offset).toISOString().slice(0, 16);
}

/**
 * Visual editor for the condition tree of a conditional policy.
 *
 * @fires input - When the tree is modified
 */
@customElement("ak-condition-builder")
export class AkConditionBuilder extends AKControlElement<ConditionTreeRequest> {
    static styles = [
        PFButton,
        PFForm,
        PFFormControl,
        PFLabel,
        css`
            .group {
                border-left: 3px solid var(--pf-global--primary-color--100);
                padding: var(--pf-global--spacer--sm) 0 var(--pf-global--spacer--sm)
                    var(--pf-global--spacer--md);
                display: flex;
                flex-direction: column;
                gap: var(--pf-global--spacer--sm);
            }
            .group.any {
                border-left-color: var(--pf-global--palette--orange-300);
            }
            .row {
                display: flex;
                flex-wrap: wrap;
                align-items: center;
                gap: var(--pf-global--spacer--sm);
            }
            .row > select,
            .row > input,
            .row > ak-search-select {
                width: auto;
                min-width: 10rem;
                max-width: 22rem;
            }
            .row .grow {
                flex: 1 1 12rem;
            }
            .item {
                display: flex;
                align-items: flex-start;
                gap: var(--pf-global--spacer--sm);
            }
            .item > .content {
                flex: 1;
            }
            .chips {
                display: flex;
                flex-wrap: wrap;
                gap: var(--pf-global--spacer--xs);
                align-items: center;
            }
            .summary {
                font-family: var(--pf-global--FontFamily--monospace);
                font-size: var(--pf-global--FontSize--sm);
                color: var(--pf-global--Color--200);
                word-break: break-word;
            }
            .warning {
                color: var(--pf-global--warning-color--200);
            }
        `,
    ];

    @property({ type: String })
    public name = "conditions";

    @property({ attribute: false })
    public catalog?: ConditionCatalog;

    /**
     * Initial value of the tree
     */
    @property({ attribute: false })
    public set value(value: ConditionTreeRequest | undefined) {
        const tree = value ? (structuredClone(value) as ConditionTreeRequest) : emptyTree();
        if (tree.root.type !== "group") {
            tree.root = { type: "group", op: "all", children: [tree.root] };
        }
        this.tree = tree;
    }

    public get value(): ConditionTreeRequest {
        return this.tree;
    }

    /**
     * Model label of the object the policy will be bound to, used to only offer variables
     * which are available there.
     */
    @state()
    protected target: string | null = null;

    @state()
    protected tree: ConditionTreeRequest = emptyTree();

    public toJSON(): ConditionTreeRequest {
        return this.tree;
    }

    protected changed() {
        this.requestUpdate();
        this.dispatchEvent(new Event("input", { bubbles: true, composed: true }));
    }

    //#region Variables

    protected get facts() {
        return factsForTarget(this.catalog, this.target);
    }

    protected renderVariableOptions(selected: string, onlyAvailable = true) {
        const facts = this.facts;
        const groups = new Map<string, ConditionVariable[]>();
        for (const variable of this.catalog?.variables ?? []) {
            if (onlyAvailable && !isAvailable(variable, facts) && variable.key !== selected) {
                continue;
            }
            const app = variable.appVerboseName || variable.app;
            groups.set(app, [...(groups.get(app) ?? []), variable]);
        }
        return html`<option value="" ?selected=${!selected} disabled>
                ${msg("Select a variable...", { id: "policies.conditional.variable.placeholder" })}
            </option>
            ${[...groups.entries()].map(
                ([app, variables]) =>
                    html`<optgroup label=${app}>
                        ${variables.map(
                            (variable) =>
                                html`<option
                                    value=${variable.key}
                                    ?selected=${variable.key === selected}
                                    title=${variable.description}
                                >
                                    ${variable.label} (${variable.key})
                                </option>`,
                        )}
                    </optgroup>`,
            )}`;
    }

    /**
     * Variable picker, including parameter and cast inputs when needed.
     */
    protected renderVariableRef(
        ref: ConditionVariableRefRequest,
        onChange: (ref: ConditionVariableRefRequest) => void,
    ) {
        const variable = findVariable(this.catalog, ref.key);
        return html`<select
                class="pf-c-form-control"
                aria-label=${msg("Variable", { id: "policies.conditional.variable.aria-label" })}
                @change=${(ev: Event) => {
                    const key = (ev.target as HTMLSelectElement).value;
                    onChange({ key, param: null, cast: null });
                }}
            >
                ${this.renderVariableOptions(ref.key)}
            </select>
            ${variable && variable.param !== ConditionParamKindEnum.None
                ? html`<input
                      type="text"
                      class="pf-c-form-control"
                      .value=${ref.param ?? ""}
                      placeholder=${variable.param === ConditionParamKindEnum.Path
                          ? msg("Path, e.g. department.name", {
                                id: "policies.conditional.variable.param-path.placeholder",
                            })
                          : msg("Key", {
                                id: "policies.conditional.variable.param-key.placeholder",
                            })}
                      @input=${(ev: InputEvent) => {
                          onChange({ ...ref, param: (ev.target as HTMLInputElement).value });
                      }}
                  />`
                : nothing}
            ${variable?.type.kind === ConditionTypeKindEnum.Any
                ? html`<select
                      class="pf-c-form-control"
                      aria-label=${msg("Treat value as", {
                          id: "policies.conditional.variable.cast.aria-label",
                      })}
                      @change=${(ev: Event) => {
                          const cast = (ev.target as HTMLSelectElement).value;
                          onChange({ ...ref, cast: cast as ConditionVariableRefRequest["cast"] });
                      }}
                  >
                      <option value="" ?selected=${!ref.cast} disabled>
                          ${msg("Treat as...", {
                              id: "policies.conditional.variable.cast.placeholder",
                          })}
                      </option>
                      ${CAST_KINDS.map(
                          (kind) =>
                              html`<option value=${kind} ?selected=${ref.cast === kind}>
                                  ${kind}
                              </option>`,
                      )}
                  </select>`
                : nothing}`;
    }

    //#endregion

    //#region Values

    protected renderModelSelect(
        model: string,
        current: unknown,
        onChange: (value: string | undefined) => void,
    ) {
        const lookup = MODEL_LOOKUPS[model];
        if (!lookup) {
            return html`<input
                type="text"
                class="pf-c-form-control"
                placeholder=${msg("Primary key", {
                    id: "policies.conditional.value.pk.placeholder",
                })}
                .value=${(current as string) ?? ""}
                @input=${(ev: InputEvent) => onChange((ev.target as HTMLInputElement).value)}
            />`;
        }
        return html`<ak-search-select
            .fetchObjects=${lookup.fetch}
            .renderElement=${lookup.render}
            .value=${lookup.value}
            .selected=${(obj: Application | Group | Source | User) => lookup.value(obj) === current}
            @ak-change=${(ev: CustomEvent<{ value: Application | Group | Source | User | null }>) =>
                onChange(lookup.value(ev.detail.value))}
        ></ak-search-select>`;
    }

    /**
     * Input for a single (non-list) value of type `type`.
     */
    protected renderScalarInput(
        type: ValueType,
        current: unknown,
        onChange: (value: unknown) => void,
    ): TemplateResult {
        const onInput = (ev: InputEvent) => onChange((ev.target as HTMLInputElement).value);
        switch (type.kind) {
            case ConditionTypeKindEnum.Number:
                return html`<input
                    type="number"
                    step="any"
                    class="pf-c-form-control"
                    .value=${current === undefined || current === null ? "" : String(current)}
                    @input=${(ev: InputEvent) => {
                        const raw = (ev.target as HTMLInputElement).value;
                        onChange(raw === "" ? null : Number(raw));
                    }}
                />`;
            case ConditionTypeKindEnum.Datetime:
                return html`<input
                    type="datetime-local"
                    class="pf-c-form-control"
                    .value=${toLocalDatetime(current)}
                    @input=${(ev: InputEvent) => {
                        const raw = (ev.target as HTMLInputElement).value;
                        onChange(raw ? new Date(raw).toISOString() : null);
                    }}
                />`;
            case ConditionTypeKindEnum.Enum:
                return html`<select
                    class="pf-c-form-control"
                    @change=${(ev: Event) => onChange((ev.target as HTMLSelectElement).value)}
                >
                    <option value="" ?selected=${!current} disabled>---------</option>
                    ${(type.choices ?? []).map(
                        (choice) =>
                            html`<option
                                value=${choice.value}
                                ?selected=${choice.value === current}
                            >
                                ${choice.label}
                            </option>`,
                    )}
                </select>`;
            case ConditionTypeKindEnum.Model:
                return this.renderModelSelect(type.model ?? "", current, onChange);
            case ConditionTypeKindEnum.Duration:
                return html`<input
                    type="text"
                    class="pf-c-form-control"
                    placeholder="hours=1;minutes=30"
                    .value=${(current as string) ?? ""}
                    @input=${onInput}
                />`;
            case ConditionTypeKindEnum.Cidr:
                return html`<input
                    type="text"
                    class="pf-c-form-control"
                    placeholder="10.0.0.0/8"
                    .value=${(current as string) ?? ""}
                    @input=${onInput}
                />`;
            default:
                return html`<input
                    type="text"
                    class="pf-c-form-control grow"
                    .value=${current === undefined || current === null ? "" : String(current)}
                    @input=${onInput}
                />`;
        }
    }

    /**
     * Editor for a list of values: the current values as removable labels, and an input to
     * add more.
     */
    protected renderListInput(
        item: ValueType,
        current: unknown,
        onChange: (value: unknown[]) => void,
    ): TemplateResult {
        const values = Array.isArray(current) ? current : [];
        let pending: unknown = null;
        const add = () => {
            if (pending === null || pending === undefined || pending === "") return;
            if (!values.includes(pending)) onChange([...values, pending]);
        };
        const label = (value: unknown) =>
            item.choices?.find((choice) => choice.value === value)?.label ?? String(value);
        return html`<div class="chips grow">
            ${values.map(
                (value, idx) =>
                    html`<span class="pf-c-label pf-m-outline">
                        <span class="pf-c-label__content">${label(value)}</span>
                        <button
                            type="button"
                            class="pf-c-button pf-m-plain pf-m-small"
                            aria-label=${msg("Remove value", {
                                id: "policies.conditional.value.remove.aria-label",
                            })}
                            @click=${() => onChange(values.filter((_, i) => i !== idx))}
                        >
                            <i class="fas fa-times" aria-hidden="true"></i>
                        </button>
                    </span>`,
            )}
            ${item.kind === ConditionTypeKindEnum.Enum || item.kind === ConditionTypeKindEnum.Model
                ? this.renderScalarInput(item, null, (value) => {
                      pending = value;
                      add();
                  })
                : html`${this.renderScalarInput(item, null, (value) => {
                          pending = value;
                      })}
                      <button
                          type="button"
                          class="pf-c-button pf-m-secondary pf-m-small"
                          @click=${(ev: Event) => {
                              add();
                              const input = (ev.target as HTMLElement)
                                  .previousElementSibling as HTMLInputElement | null;
                              if (input) input.value = "";
                          }}
                      >
                          ${msg("Add", { id: "policies.conditional.value.add.label" })}
                      </button>`}
        </div>`;
    }

    protected renderOperand(node: Condition, type: ValueType | null) {
        const operator = this.catalog?.operators.find((op) => op.name === node.operator);
        const expected = operandType(operator, type);
        if (!expected) return nothing;
        const isVariable = node.value?.type === "variable";
        const setLiteral = (value: unknown) => {
            node.value = { type: "literal", value };
            this.changed();
        };
        const current = node.value?.type === "literal" ? node.value.value : undefined;
        let editor: TemplateResult;
        if (isVariable && node.value?.type === "variable") {
            editor = html`${this.renderVariableRef(node.value.variable, (variable) => {
                node.value = { type: "variable", variable };
                this.changed();
            })}`;
        } else if (operator?.operand === "range") {
            const values = Array.isArray(current) ? current : [null, null];
            editor = html`${this.renderScalarInput(type!, values[0], (value) =>
                setLiteral([value, values[1]]),
            )}
            ${msg("and", { id: "policies.conditional.value.range.separator" })}
            ${this.renderScalarInput(type!, values[1], (value) => setLiteral([values[0], value]))}`;
        } else if (expected.kind === ConditionTypeKindEnum.List && expected.item) {
            editor = this.renderListInput(expected.item, current, setLiteral);
        } else {
            editor = this.renderScalarInput(expected, current, setLiteral);
        }
        return html`<select
                class="pf-c-form-control"
                aria-label=${msg("Compare with", {
                    id: "policies.conditional.value.source.aria-label",
                })}
                @change=${(ev: Event) => {
                    const source = (ev.target as HTMLSelectElement).value;
                    node.value =
                        source === "variable"
                            ? { type: "variable", variable: { key: "" } }
                            : { type: "literal", value: null };
                    this.changed();
                }}
            >
                <option value="literal" ?selected=${!isVariable}>
                    ${msg("value", { id: "policies.conditional.value.source.literal" })}
                </option>
                <option value="variable" ?selected=${isVariable}>
                    ${msg("variable", { id: "policies.conditional.value.source.variable" })}
                </option>
            </select>
            ${editor}`;
    }

    //#endregion

    //#region Nodes

    protected renderCondition(node: Condition) {
        const type = variableType(this.catalog, node.variable);
        const operators = operatorsFor(this.catalog, type);
        const variable = findVariable(this.catalog, node.variable.key);
        const facts = this.facts;
        return html`<div class="row">
            ${this.renderVariableRef(node.variable, (ref) => {
                node.variable = ref;
                const newType = variableType(this.catalog, ref);
                const valid = operatorsFor(this.catalog, newType).some(
                    (op) => op.name === node.operator,
                );
                if (!valid) node.operator = ConditionOperatorEnum.IsSet;
                node.value = null;
                this.changed();
            })}
            <select
                class="pf-c-form-control"
                aria-label=${msg("Operator", { id: "policies.conditional.operator.aria-label" })}
                ?disabled=${!type}
                @change=${(ev: Event) => {
                    const previous = operandType(
                        this.catalog?.operators.find((op) => op.name === node.operator),
                        type,
                    );
                    node.operator = (ev.target as HTMLSelectElement).value as ConditionOperatorEnum;
                    const next = operandType(
                        this.catalog?.operators.find((op) => op.name === node.operator),
                        type,
                    );
                    // Keep the value if the operand has the same shape
                    if (!next || JSON.stringify(previous) !== JSON.stringify(next)) {
                        node.value = null;
                    }
                    this.changed();
                }}
            >
                ${operators.map(
                    (op) =>
                        html`<option value=${op.name} ?selected=${op.name === node.operator}>
                            ${op.label}
                        </option>`,
                )}
            </select>
            ${this.renderOperand(node, type)}
            ${isTextual(type) && node.operator !== ConditionOperatorEnum.IsSet
                ? html`<label>
                      <input
                          type="checkbox"
                          .checked=${node.options?.caseSensitive === false}
                          @change=${(ev: Event) => {
                              node.options = {
                                  caseSensitive: !(ev.target as HTMLInputElement).checked,
                              };
                              this.changed();
                          }}
                      />
                      ${msg("Ignore case", { id: "policies.conditional.options.ignore-case" })}
                  </label>`
                : nothing}
            ${variable && !isAvailable(variable, facts)
                ? html`<span class="warning">
                      <i class="fas fa-exclamation-triangle" aria-hidden="true"></i>
                      ${msg("Not available for the selected object", {
                          id: "policies.conditional.variable.unavailable",
                      })}
                  </span>`
                : nothing}
        </div>`;
    }

    protected renderPolicyRef(node: ConditionNodeRequest & { type: "policy" }) {
        return html`<div class="row">
            <span>${msg("Policy passes", { id: "policies.conditional.policy.label" })}</span>
            <ak-search-select
                .fetchObjects=${async (search?: string): Promise<Policy[]> =>
                    (await aki(PoliciesApi).policiesAllList({ search, ordering: "name" })).results}
                .renderElement=${(policy: Policy) => policy.name}
                .value=${(policy: Policy | null) => policy?.pk}
                .selected=${(policy: Policy) => policy.pk === node.policy}
                @ak-change=${(ev: CustomEvent<{ value: Policy | null }>) => {
                    node.policy = ev.detail.value?.pk ?? "";
                    this.changed();
                }}
            ></ak-search-select>
        </div>`;
    }

    /**
     * Render a child of a group, with controls to negate or remove it.
     */
    protected renderChild(parent: GroupNode, index: number): TemplateResult {
        const child = parent.children[index];
        const negated = child.type === "not";
        const inner = negated ? child.child : child;
        let content: TemplateResult;
        switch (inner.type) {
            case "group":
                content = this.renderGroup(inner as GroupNode);
                break;
            case "policy":
                content = this.renderPolicyRef(inner);
                break;
            case "condition":
                content = this.renderCondition(inner as Condition);
                break;
            default:
                content = html`${msg("Unsupported node", {
                    id: "policies.conditional.node.unsupported",
                })}`;
        }
        return html`<div class="item">
            <button
                type="button"
                class="pf-c-button pf-m-small ${negated ? "pf-m-danger" : "pf-m-tertiary"}"
                title=${msg("Negate", { id: "policies.conditional.node.negate.tooltip" })}
                @click=${() => {
                    parent.children[index] = negated ? inner : { type: "not", child: inner };
                    this.changed();
                }}
            >
                ${msg("NOT", { id: "policies.conditional.node.negate.label" })}
            </button>
            <div class="content">${content}</div>
            <button
                type="button"
                class="pf-c-button pf-m-plain"
                aria-label=${msg("Remove", { id: "policies.conditional.node.remove.aria-label" })}
                @click=${() => {
                    parent.children.splice(index, 1);
                    this.changed();
                }}
            >
                <i class="fas fa-trash" aria-hidden="true"></i>
            </button>
        </div>`;
    }

    protected renderGroup(group: GroupNode): TemplateResult {
        const add = (node: ConditionNodeRequest) => {
            group.children.push(node);
            this.changed();
        };
        return html`<div class="group ${group.op}">
            <div class="row">
                <select
                    class="pf-c-form-control"
                    aria-label=${msg("Group operator", {
                        id: "policies.conditional.group.op.aria-label",
                    })}
                    @change=${(ev: Event) => {
                        group.op = (ev.target as HTMLSelectElement).value as GroupNode["op"];
                        this.changed();
                    }}
                >
                    <option value="all" ?selected=${group.op === "all"}>
                        ${msg("All of the following", { id: "policies.conditional.group.op.all" })}
                    </option>
                    <option value="any" ?selected=${group.op === "any"}>
                        ${msg("Any of the following", { id: "policies.conditional.group.op.any" })}
                    </option>
                </select>
            </div>
            ${group.children.map((_, index) => this.renderChild(group, index))}
            <div class="row">
                <button
                    type="button"
                    class="pf-c-button pf-m-link pf-m-small"
                    @click=${() => add(newCondition())}
                >
                    <i class="fas fa-plus" aria-hidden="true"></i>
                    ${msg("Condition", { id: "policies.conditional.group.add-condition" })}
                </button>
                <button
                    type="button"
                    class="pf-c-button pf-m-link pf-m-small"
                    @click=${() => add({ type: "group", op: "any", children: [newCondition()] })}
                >
                    <i class="fas fa-plus" aria-hidden="true"></i>
                    ${msg("Group", { id: "policies.conditional.group.add-group" })}
                </button>
                <button
                    type="button"
                    class="pf-c-button pf-m-link pf-m-small"
                    @click=${() => add({ type: "policy", policy: "" })}
                >
                    <i class="fas fa-plus" aria-hidden="true"></i>
                    ${msg("Policy", { id: "policies.conditional.group.add-policy" })}
                </button>
            </div>
        </div>`;
    }

    //#endregion

    protected renderTargetSelect() {
        return html`<div class="row">
            <label for="target"
                >${msg("Used with", { id: "policies.conditional.target.label" })}</label
            >
            <select
                id="target"
                class="pf-c-form-control"
                @change=${(ev: Event) => {
                    this.target = (ev.target as HTMLSelectElement).value || null;
                }}
            >
                <option value="" ?selected=${!this.target}>
                    ${msg("Any object (show all variables)", {
                        id: "policies.conditional.target.any",
                    })}
                </option>
                ${(this.catalog?.targets ?? []).map(
                    (target) =>
                        html`<option
                            value=${target.model}
                            ?selected=${target.model === this.target}
                        >
                            ${target.verboseName}
                        </option>`,
                )}
            </select>
        </div>`;
    }

    render() {
        if (!this.catalog) {
            return html`<ak-spinner></ak-spinner>`;
        }
        const root = this.tree.root as GroupNode;
        const unavailable = unavailableVariables(this.catalog, root, this.facts);
        return html`<div class="pf-c-form">
            ${this.renderTargetSelect()} ${this.renderGroup(root)}
            ${unavailable.length
                ? html`<p class="warning">
                      ${msg("These variables are not available for the selected object:", {
                          id: "policies.conditional.target.unavailable",
                      })}
                      ${unavailable.join(", ")}
                  </p>`
                : nothing}
            ${root.children.length
                ? html`<p class="summary">${describe(this.catalog, root)}</p>`
                : nothing}
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-condition-builder": AkConditionBuilder;
    }
}

import "#elements/Spinner";
import "#elements/forms/SearchSelect/index";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLabel from "@patternfly/patternfly/components/Label/label.css";

import { aki } from "#common/api/client";
import { groupBy } from "#common/utils";

import { AKControlElement } from "#elements/ControlElement";

import {
    assignErrors,
    CAST_KINDS,
    collectNodePaths,
    ConditionErrors,
    describe,
    emptyTree,
    errorOwner,
    factsForTarget,
    filterPickerOptions,
    findVariable,
    isAvailable,
    isTextual,
    newCondition,
    operandType,
    operatorChoiceId,
    operatorChoices,
    operatorsFor,
    PickerOption,
    pickerOptionId,
    pickerOptions,
    removeNotNodes,
    ValueType,
    variableType,
} from "#admin/policies/conditional/utils";

import {
    Application,
    ConditionCatalog,
    ConditionComparisonNode,
    ConditionGroupNode,
    ConditionNode,
    ConditionOperatorName,
    ConditionParamKindEnum,
    ConditionPolicyNode,
    ConditionTree,
    ConditionTypeKindEnum,
    ConditionVariableRef,
    CoreApi,
    Group,
    PoliciesApi,
    Policy,
    Source,
    SourcesApi,
    User,
} from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { css, html, nothing, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

type Condition = ConditionComparisonNode & { type: "condition" };

type GroupNode = ConditionGroupNode & { type: "group" };

type PolicyNode = ConditionPolicyNode & { type: "policy" };

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

const CAST_LABELS: Record<string, string> = {
    string: msg("as text", { id: "policies.conditional.cast.string" }),
    number: msg("as number", { id: "policies.conditional.cast.number" }),
    boolean: msg("as yes/no", { id: "policies.conditional.cast.boolean" }),
    datetime: msg("as date", { id: "policies.conditional.cast.datetime" }),
    ip: msg("as IP address", { id: "policies.conditional.cast.ip" }),
};

const TYPE_LABELS: Record<string, string> = {
    string: msg("text", { id: "policies.conditional.type.string" }),
    number: msg("number", { id: "policies.conditional.type.number" }),
    boolean: msg("yes/no", { id: "policies.conditional.type.boolean" }),
    datetime: msg("date", { id: "policies.conditional.type.datetime" }),
    ip: msg("IP address", { id: "policies.conditional.type.ip" }),
    enum: msg("choice", { id: "policies.conditional.type.enum" }),
    model: msg("object", { id: "policies.conditional.type.model" }),
    any: msg("any value", { id: "policies.conditional.type.any" }),
};

function typeLabel(type: ValueType): string {
    if (type.kind === ConditionTypeKindEnum.List && type.item) {
        return msg(str`list of ${typeLabel(type.item)}`, { id: "policies.conditional.type.list" });
    }

    return TYPE_LABELS[type.kind] ?? type.kind;
}

function toLocalDatetime(value: unknown): string {
    if (typeof value !== "string" || !value) return "";

    const date = new Date(value);

    if (isNaN(date.getTime())) return "";

    const offset = date.getTimezoneOffset() * 60_000;

    return new Date(date.getTime() - offset).toISOString().slice(0, 16);
}

/**
 * Visual editor for the condition tree of a conditional policy. Each condition is shown as a
 * row which reads like a sentence, less common options are in a menu per row.
 *
 * @fires input - When the tree is modified
 */
@customElement("ak-condition-builder")
export class AkConditionBuilder extends AKControlElement<ConditionTree> {
    static styles = [
        PFButton,
        PFForm,
        PFFormControl,
        PFLabel,
        css`
            :host {
                display: block;
            }
            .builder {
                border: 1px solid var(--pf-global--BorderColor--100);
                background: var(--pf-global--BackgroundColor--200);
                padding: var(--pf-global--spacer--md);
                display: flex;
                flex-direction: column;
                gap: var(--pf-global--spacer--sm);
            }
            .toolbar,
            .sentence {
                display: flex;
                align-items: center;
                gap: var(--pf-global--spacer--sm);
                flex-wrap: wrap;
            }
            .toolbar {
                justify-content: space-between;
            }
            .toolbar .target {
                white-space: nowrap;
                display: flex;
                align-items: center;
                gap: var(--pf-global--spacer--sm);
                color: var(--pf-global--Color--200);
                font-size: var(--pf-global--FontSize--sm);
            }
            select.op-select {
                width: auto;
                font-weight: var(--pf-global--FontWeight--bold);
                color: var(--pf-global--primary-color--100);
            }
            .rows {
                display: flex;
                flex-direction: column;
                gap: var(--pf-global--spacer--sm);
            }
            .row {
                position: relative;
                background: var(--pf-global--BackgroundColor--100);
                border: 1px solid var(--pf-global--BorderColor--100);
                border-radius: var(--pf-global--BorderRadius--sm);
                padding: var(--pf-global--spacer--sm);
                display: grid;
                grid-template-columns: 1fr auto;
                gap: var(--pf-global--spacer--xs) var(--pf-global--spacer--sm);
            }
            .row.invalid {
                border-color: var(--pf-global--danger-color--100);
            }
            .row.group {
                border-left: 3px solid var(--pf-global--palette--orange-300);
            }
            .row.group.none {
                border-left-color: var(--pf-global--danger-color--100);
            }
            .row .details {
                grid-column: 1 / -1;
            }
            .parts {
                display: flex;
                flex-wrap: wrap;
                align-items: center;
                gap: var(--pf-global--spacer--sm);
            }
            .parts > select,
            .parts > input {
                flex: 0 1 auto;
                width: auto;
                max-width: 16rem;
            }
            .parts > ak-search-select {
                flex: 0 1 15rem;
                min-width: 11rem;
            }
            .parts > .value {
                flex: 1 1 9rem;
                min-width: 9rem;
                max-width: 24rem;
            }
            .parts > .chips.value {
                flex: 1 1 16rem;
                max-width: none;
            }
            .chips input {
                width: 7rem;
                flex: 0 1 7rem;
            }
            .tag {
                font-size: var(--pf-global--FontSize--xs);
                color: var(--pf-global--Color--200);
                background: var(--pf-global--BackgroundColor--200);
                border-radius: var(--pf-global--BorderRadius--sm);
                padding: 0 var(--pf-global--spacer--xs);
            }
            .chips {
                display: flex;
                flex-wrap: wrap;
                gap: var(--pf-global--spacer--xs);
                align-items: center;
            }
            .menu {
                position: absolute;
                right: 0;
                top: calc(100% + 2px);
                z-index: 10;
                min-width: 16rem;
                background: var(--pf-global--BackgroundColor--100);
                border: 1px solid var(--pf-global--BorderColor--100);
                box-shadow: var(--pf-global--BoxShadow--md);
                padding: var(--pf-global--spacer--xs) 0;
            }
            .menu button {
                display: flex;
                gap: var(--pf-global--spacer--sm);
                align-items: center;
                width: 100%;
                text-align: left;
                background: none;
                border: none;
                padding: var(--pf-global--spacer--sm) var(--pf-global--spacer--md);
                font: inherit;
                color: inherit;
                cursor: pointer;
            }
            .menu button:hover {
                background: var(--pf-global--BackgroundColor--200);
            }
            .menu button.danger {
                color: var(--pf-global--danger-color--100);
            }
            .menu hr {
                border: none;
                border-top: 1px solid var(--pf-global--BorderColor--100);
                margin: var(--pf-global--spacer--xs) 0;
            }
            .menu .icon {
                width: 1rem;
                text-align: center;
            }
            .add {
                display: flex;
                flex-wrap: wrap;
                gap: var(--pf-global--spacer--xs);
            }
            .summary {
                background: var(--pf-global--BackgroundColor--100);
                border: 1px dashed var(--pf-global--BorderColor--100);
                border-radius: var(--pf-global--BorderRadius--sm);
                padding: var(--pf-global--spacer--sm) var(--pf-global--spacer--md);
                font-size: var(--pf-global--FontSize--sm);
                word-break: break-word;
            }
            .empty {
                color: var(--pf-global--Color--200);
                padding: var(--pf-global--spacer--sm) 0;
            }
            .warning {
                color: var(--pf-global--warning-color--200);
                font-size: var(--pf-global--FontSize--sm);
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
    public set value(value: ConditionTree | undefined) {
        const tree = value ? (structuredClone(value) as ConditionTree) : emptyTree();

        if (tree.root.type !== "group") {
            tree.root = { type: "group", op: "all", children: [tree.root] };
        }

        this.tree = tree;
        this.#normalized = false;
    }

    public get value(): ConditionTree {
        return this.tree;
    }

    /**
     * Validation errors returned by the API, keyed by the path of the node they belong to.
     */
    @property({ attribute: false })
    public errors: ConditionErrors = {};

    /**
     * Model label of the object the policy will be bound to, used to only offer variables
     * which are available there.
     */
    @state()
    protected target: string | null = null;

    @state()
    protected tree: ConditionTree = emptyTree();

    /**
     * The node whose menu is open.
     */
    @state()
    protected openMenu: ConditionNode | null = null;

    /**
     * Whether `not` nodes have been replaced, which requires the catalog.
     */
    #normalized = false;

    /**
     * Paths of all nodes as of the last render, used to find the node errors belong to.
     */
    #paths = new Map<ConditionNode, string>();

    #ownedErrors = new Map<string, string[]>();

    #closeMenu = () => {
        this.openMenu = null;
    };

    public override connectedCallback(): void {
        super.connectedCallback();
        document.addEventListener("click", this.#closeMenu);
    }

    public override disconnectedCallback(): void {
        document.removeEventListener("click", this.#closeMenu);
        super.disconnectedCallback();
    }

    public toJSON(): ConditionTree {
        return this.tree;
    }

    /**
     * Called when the tree was modified. When a single `node` was edited, only its errors are
     * cleared. Otherwise the structure changed, and as paths of nodes may have changed, all
     * errors are cleared.
     */
    protected changed(node?: ConditionNode) {
        const path = node ? this.#paths.get(node) : undefined;

        if (path === undefined) {
            this.errors = {};
        } else {
            const paths = [...this.#paths.values()];

            this.errors = Object.fromEntries(
                Object.entries(this.errors).filter(([key]) => errorOwner(key, paths) !== path),
            );
        }

        this.openMenu = null;
        this.requestUpdate();
        this.dispatchEvent(new Event("input", { bubbles: true, composed: true }));
    }

    protected nodeErrors(node: ConditionNode): string[] {
        const path = this.#paths.get(node);

        return path === undefined ? [] : (this.#ownedErrors.get(path) ?? []);
    }

    protected renderErrors(errors: string[]) {
        return errors.map(
            (error) =>
                html`<p class="pf-c-form__helper-text pf-m-error" role="alert">
                    <span class="pf-c-form__helper-text-icon">
                        <i class="fas fa-exclamation-circle" aria-hidden="true"></i>
                    </span>
                    ${error}
                </p>`,
        );
    }

    protected get facts() {
        return factsForTarget(this.catalog, this.target);
    }

    //#region Variables

    /**
     * Search select to pick a variable, or a well-defined parameter of a variable.
     */
    protected renderVariablePicker(
        ref: ConditionVariableRef,
        onChange: (ref: ConditionVariableRef) => void,
    ) {
        const options = pickerOptions(this.catalog, this.facts);
        const selectedId = ref.key ? pickerOptionId(ref) : null;
        const variable = findVariable(this.catalog, ref.key);
        const isKnown = !!variable?.params.some((param) => param.key === ref.param);

        // Values with a custom path are shown as the "custom path" entry
        const currentId =
            ref.key && !isKnown ? pickerOptionId({ key: ref.key, param: null }) : selectedId;

        return html`<ak-search-select
            placeholder=${msg("Choose a value...", {
                id: "policies.conditional.variable.placeholder",
            })}
            .fetchObjects=${async (query?: string) =>
                filterPickerOptions(
                    options.filter((option) => option.available || option.id === currentId),
                    query,
                )}
            .groupBy=${(items: PickerOption[]) => groupBy(items, (option) => option.category)}
            .renderElement=${(option: PickerOption) => `${option.category} › ${option.label}`}
            .renderDescription=${(option: PickerOption) =>
                html`<code>${option.param ? `${option.key}.${option.param}` : option.key}</code> ·
                    ${typeLabel(option.type)}`}
            .value=${(option: PickerOption | null) => option?.id}
            .selected=${(option: PickerOption) => option.id === currentId}
            @ak-change=${(ev: CustomEvent<{ value: PickerOption | null }>) => {
                const option = ev.detail.value;

                if (!option || option.id === currentId) return;

                onChange({ key: option.key, param: option.param, cast: null });
            }}
        ></ak-search-select>`;
    }

    /**
     * Inputs for the parameter (for example an attribute path) and type of a variable, when
     * they're not defined by the variable.
     */
    protected renderVariableDetails(
        ref: ConditionVariableRef,
        onChange: (ref: ConditionVariableRef) => void,
    ) {
        const variable = findVariable(this.catalog, ref.key);

        if (!variable) return nothing;

        const known = variable.params.find((param) => param.key === ref.param);

        if (known) return nothing;

        const param =
            variable.param !== ConditionParamKindEnum.None
                ? html`<input
                      type="text"
                      class="pf-c-form-control"
                      .value=${ref.param ?? ""}
                      placeholder=${
                          variable.param === ConditionParamKindEnum.Path
                              ? msg("Path, e.g. department.name", {
                                    id: "policies.conditional.variable.param-path.placeholder",
                                })
                              : msg("Field key", {
                                    id: "policies.conditional.variable.param-key.placeholder",
                                })
                      }
                      aria-label=${msg("Path or key", {
                          id: "policies.conditional.variable.param.aria-label",
                      })}
                      @input=${(ev: InputEvent) => {
                          onChange({ ...ref, param: (ev.target as HTMLInputElement).value });
                      }}
                  />`
                : nothing;

        const cast =
            variable.type.kind === ConditionTypeKindEnum.Any
                ? html`<select
                      class="pf-c-form-control"
                      aria-label=${msg("Type of the value", {
                          id: "policies.conditional.variable.cast.aria-label",
                      })}
                      @change=${(ev: Event) => {
                          const value = (ev.target as HTMLSelectElement).value;

                          onChange({
                              ...ref,
                              cast: (value || null) as ConditionVariableRef["cast"],
                          });
                      }}
                  >
                      <option value="" ?selected=${!ref.cast}>
                          ${msg("as any value", { id: "policies.conditional.cast.none" })}
                      </option>
                      ${CAST_KINDS.map(
                          (kind) =>
                              html`<option value=${kind} ?selected=${ref.cast === kind}>
                                  ${CAST_LABELS[kind] ?? kind}
                              </option>`,
                      )}
                  </select>`
                : nothing;

        return html`${param} ${cast}`;
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
                class="pf-c-form-control value"
                placeholder=${msg("Primary key", {
                    id: "policies.conditional.value.pk.placeholder",
                })}
                .value=${(current as string) ?? ""}
                @input=${(ev: InputEvent) => onChange((ev.target as HTMLInputElement).value)}
            />`;
        }

        return html`<ak-search-select
            class="value"
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
                    class="pf-c-form-control value"
                    .value=${current === undefined || current === null ? "" : String(current)}
                    @input=${(ev: InputEvent) => {
                        const raw = (ev.target as HTMLInputElement).value;

                        onChange(raw === "" ? null : Number(raw));
                    }}
                />`;
            case ConditionTypeKindEnum.Datetime:
                return html`<input
                    type="datetime-local"
                    class="pf-c-form-control value"
                    .value=${toLocalDatetime(current)}
                    @input=${(ev: InputEvent) => {
                        const raw = (ev.target as HTMLInputElement).value;

                        onChange(raw ? new Date(raw).toISOString() : null);
                    }}
                />`;
            case ConditionTypeKindEnum.Enum:
                return html`<select
                    class="pf-c-form-control value"
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
                    class="pf-c-form-control value"
                    placeholder="hours=1;minutes=30"
                    .value=${(current as string) ?? ""}
                    @input=${onInput}
                />`;
            case ConditionTypeKindEnum.Cidr:
                return html`<input
                    type="text"
                    class="pf-c-form-control value"
                    placeholder="10.0.0.0/8"
                    .value=${(current as string) ?? ""}
                    @input=${onInput}
                />`;
            default:
                return html`<input
                    type="text"
                    class="pf-c-form-control value"
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

        const input =
            item.kind === ConditionTypeKindEnum.Enum || item.kind === ConditionTypeKindEnum.Model
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

                              const previous = (ev.target as HTMLElement)
                                  .previousElementSibling as HTMLInputElement | null;

                              if (previous) previous.value = "";
                          }}
                      >
                          ${msg("Add", { id: "policies.conditional.value.add.label" })}
                      </button>`;

        return html`<div class="chips value">
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
            ${input}
        </div>`;
    }

    protected renderOperand(node: Condition, type: ValueType | null) {
        const operator = this.catalog?.operators.find((op) => op.name === node.operator);
        const expected = operandType(operator, type);

        if (!expected) return nothing;

        if (node.value?.type === "variable") {
            const ref = node.value.variable;

            return html`${this.renderVariablePicker(ref, (variable) => {
                node.value = { type: "variable", variable };
                this.changed(node);
            })}
            ${this.renderVariableDetails(ref, (variable) => {
                node.value = { type: "variable", variable };
                this.changed(node);
            })}`;
        }

        const setLiteral = (value: unknown) => {
            node.value = { type: "literal", value };
            this.changed(node);
        };

        const current = node.value?.type === "literal" ? node.value.value : undefined;

        if (operator?.operand === "range" && type) {
            const values = Array.isArray(current) ? current : [null, null];

            return html`${this.renderScalarInput(type, values[0], (value) =>
                    setLiteral([value, values[1]]),
                )}
                <span>${msg("and", { id: "policies.conditional.value.range.separator" })}</span>
                ${this.renderScalarInput(type, values[1], (value) => setLiteral([values[0], value]))}`;
        }

        if (expected.kind === ConditionTypeKindEnum.List && expected.item) {
            return this.renderListInput(expected.item, current, setLiteral);
        }

        return this.renderScalarInput(expected, current, setLiteral);
    }

    //#endregion

    //#region Menus

    protected renderMenuButton(node: ConditionNode) {
        return html`<button
            type="button"
            class="pf-c-button pf-m-plain"
            aria-label=${msg("Actions", { id: "policies.conditional.menu.aria-label" })}
            aria-expanded=${this.openMenu === node ? "true" : "false"}
            @click=${(ev: Event) => {
                ev.stopPropagation();
                this.openMenu = this.openMenu === node ? null : node;
            }}
        >
            <i class="fas fa-ellipsis-h" aria-hidden="true"></i>
        </button>`;
    }

    protected renderMenuItem(
        icon: string,
        label: string,
        action: () => void,
        className = "",
    ): TemplateResult {
        return html`<button
            type="button"
            role="menuitem"
            class=${className}
            @click=${(ev: Event) => {
                ev.stopPropagation();
                action();
            }}
        >
            <span class="icon"><i class="fas ${icon}" aria-hidden="true"></i></span>${label}
        </button>`;
    }

    /**
     * Actions shared by all nodes in a group.
     */
    protected renderCommonMenuItems(parent: GroupNode, index: number): TemplateResult {
        const node = parent.children[index];

        return html`${this.renderMenuItem(
                "fa-object-group",
                msg("Wrap in group", { id: "policies.conditional.menu.wrap" }),
                () => {
                    parent.children[index] = { type: "group", op: "any", children: [node] };
                    this.changed();
                },
            )}
            ${this.renderMenuItem(
                "fa-copy",
                msg("Duplicate", { id: "policies.conditional.menu.duplicate" }),
                () => {
                    parent.children.splice(index + 1, 0, structuredClone(node));
                    this.changed();
                },
            )}
            <hr />
            ${this.renderMenuItem(
                "fa-trash",
                msg("Delete", { id: "policies.conditional.menu.delete" }),
                () => {
                    parent.children.splice(index, 1);
                    this.changed();
                },
                "danger",
            )}`;
    }

    protected renderConditionMenu(parent: GroupNode, index: number, node: Condition) {
        if (this.openMenu !== node) return nothing;

        const type = variableType(this.catalog, node.variable);
        const operator = this.catalog?.operators.find((op) => op.name === node.operator);
        const comparesVariable = node.value?.type === "variable";

        return html`<div class="menu" role="menu">
            ${
                isTextual(type)
                    ? this.renderMenuItem(
                          node.options?.caseSensitive === false ? "fa-check" : "",
                          msg("Ignore upper/lower case", {
                              id: "policies.conditional.menu.ignore-case",
                          }),
                          () => {
                              node.options = {
                                  ...node.options,
                                  caseSensitive: node.options?.caseSensitive === false,
                              };

                              this.changed(node);
                          },
                      )
                    : nothing
            }
            ${
                operandType(operator, type)
                    ? this.renderMenuItem(
                          "fa-exchange-alt",
                          comparesVariable
                              ? msg("Compare with a fixed value", {
                                    id: "policies.conditional.menu.compare-literal",
                                })
                              : msg("Compare with another value", {
                                    id: "policies.conditional.menu.compare-variable",
                                }),
                          () => {
                              node.value = comparesVariable
                                  ? { type: "literal", value: null }
                                  : { type: "variable", variable: { key: "" } };

                              this.changed(node);
                          },
                      )
                    : nothing
            }
            ${this.renderCommonMenuItems(parent, index)}
        </div>`;
    }

    protected renderGroupMenu(parent: GroupNode, index: number, node: GroupNode) {
        if (this.openMenu !== node) return nothing;

        return html`<div class="menu" role="menu">
            ${this.renderMenuItem(
                "fa-object-ungroup",
                msg("Ungroup", { id: "policies.conditional.menu.ungroup" }),
                () => {
                    parent.children.splice(index, 1, ...node.children);
                    this.changed();
                },
            )}
            ${this.renderCommonMenuItems(parent, index)}
        </div>`;
    }

    //#endregion

    //#region Nodes

    protected renderCondition(parent: GroupNode, index: number, node: Condition) {
        const type = variableType(this.catalog, node.variable);
        const choices = operatorChoices(this.catalog, type);
        const variable = findVariable(this.catalog, node.variable.key);
        const errors = this.nodeErrors(node);
        const selectedChoice = operatorChoiceId(node.operator, node.options?.negate);

        return html`<div class="row ${errors.length ? "invalid" : ""}">
            <div class="parts">
                ${this.renderVariablePicker(node.variable, (ref) => {
                    node.variable = ref;

                    const valid = operatorsFor(this.catalog, variableType(this.catalog, ref)).some(
                        (op) => op.name === node.operator,
                    );

                    if (!valid) {
                        node.operator = ConditionOperatorName.IsSet;
                        node.options = { ...node.options, negate: false };
                    }

                    node.value = null;
                    this.changed(node);
                })}
                ${this.renderVariableDetails(node.variable, (ref) => {
                    node.variable = ref;
                    this.changed(node);
                })}
                <select
                    class="pf-c-form-control"
                    aria-label=${msg("Comparison", {
                        id: "policies.conditional.operator.aria-label",
                    })}
                    ?disabled=${!type}
                    @change=${(ev: Event) => {
                        const choice = choices.find(
                            (c) => c.id === (ev.target as HTMLSelectElement).value,
                        );

                        if (!choice) return;

                        const previous = operandType(
                            this.catalog?.operators.find((op) => op.name === node.operator),
                            type,
                        );

                        node.operator = choice.name;
                        node.options = { ...node.options, negate: choice.negate };

                        const next = operandType(
                            this.catalog?.operators.find((op) => op.name === node.operator),
                            type,
                        );

                        // Keep the value if the operand has the same shape
                        if (!next || JSON.stringify(previous) !== JSON.stringify(next)) {
                            node.value = null;
                        }

                        this.changed(node);
                    }}
                >
                    ${choices.map(
                        (choice) =>
                            html`<option
                                value=${choice.id}
                                ?selected=${choice.id === selectedChoice}
                            >
                                ${choice.label}
                            </option>`,
                    )}
                </select>
                ${this.renderOperand(node, type)}
                ${
                    isTextual(type) && node.options?.caseSensitive === false
                        ? html`<span class="tag">
                              ${msg("Aa ignored", { id: "policies.conditional.ignore-case.tag" })}
                          </span>`
                        : nothing
                }
            </div>
            <div>${this.renderMenuButton(node)}</div>
            ${this.renderConditionMenu(parent, index, node)}
            <div class="details">
                ${
                    variable && !isAvailable(variable, this.facts)
                        ? html`<p class="warning">
                              <i class="fas fa-exclamation-triangle" aria-hidden="true"></i>
                              ${msg("Not available for the selected object", {
                                  id: "policies.conditional.variable.unavailable",
                              })}
                          </p>`
                        : nothing
                }
                ${this.renderErrors(errors)}
            </div>
        </div>`;
    }

    protected renderPolicyRef(parent: GroupNode, index: number, node: PolicyNode) {
        const errors = this.nodeErrors(node);

        return html`<div class="row ${errors.length ? "invalid" : ""}">
            <div class="parts">
                <span>${msg("The policy", { id: "policies.conditional.policy.prefix" })}</span>
                <ak-search-select
                    .fetchObjects=${async (search?: string): Promise<Policy[]> =>
                        (await aki(PoliciesApi).policiesAllList({ search, ordering: "name" }))
                            .results}
                    .renderElement=${(policy: Policy) => policy.name}
                    .value=${(policy: Policy | null) => policy?.pk}
                    .selected=${(policy: Policy) => policy.pk === node.policy}
                    @ak-change=${(ev: CustomEvent<{ value: Policy | null }>) => {
                        node.policy = ev.detail.value?.pk ?? "";
                        this.changed(node);
                    }}
                ></ak-search-select>
                <span>${msg("passes", { id: "policies.conditional.policy.suffix" })}</span>
            </div>
            <div>${this.renderMenuButton(node)}</div>
            ${
                this.openMenu === node
                    ? html`<div class="menu" role="menu">
                          ${this.renderCommonMenuItems(parent, index)}
                      </div>`
                    : nothing
            }
            <div class="details">${this.renderErrors(errors)}</div>
        </div>`;
    }

    protected renderGroupOp(group: GroupNode) {
        return html`<select
            class="pf-c-form-control op-select"
            aria-label=${msg("How conditions are combined", {
                id: "policies.conditional.group.op.aria-label",
            })}
            @change=${(ev: Event) => {
                group.op = (ev.target as HTMLSelectElement).value as GroupNode["op"];
                this.changed(group);
            }}
        >
            <option value="all" ?selected=${group.op === "all"}>
                ${msg("all", { id: "policies.conditional.group.op.all" })}
            </option>
            <option value="any" ?selected=${group.op === "any"}>
                ${msg("any", { id: "policies.conditional.group.op.any" })}
            </option>
            <option value="none" ?selected=${group.op === "none"}>
                ${msg("none", { id: "policies.conditional.group.op.none" })}
            </option>
        </select>`;
    }

    protected renderChildren(group: GroupNode): TemplateResult {
        return html`<div class="rows">
            ${group.children.map((child, index) => {
                switch (child.type) {
                    case "group":
                        return this.renderNestedGroup(group, index, child as GroupNode);
                    case "policy":
                        return this.renderPolicyRef(group, index, child as PolicyNode);
                    case "condition":
                        return this.renderCondition(group, index, child as Condition);
                    default:
                        // `not` nodes are replaced when the catalog is loaded
                        return nothing;
                }
            })}
        </div>`;
    }

    protected renderNestedGroup(parent: GroupNode, index: number, group: GroupNode) {
        const errors = this.nodeErrors(group);

        return html`<div class="row group ${group.op} ${errors.length ? "invalid" : ""}">
            <div class="sentence">
                ${this.renderGroupOp(group)}
                <span
                    >${msg("of these are true", { id: "policies.conditional.group.suffix" })}</span
                >
            </div>
            <div>${this.renderMenuButton(group)}</div>
            ${this.renderGroupMenu(parent, index, group)}
            <div class="details">
                ${this.renderChildren(group)} ${this.renderErrors(errors)}
                <button
                    type="button"
                    class="pf-c-button pf-m-link pf-m-small"
                    @click=${() => {
                        group.children.push(newCondition());
                        this.changed();
                    }}
                >
                    <i class="fas fa-plus" aria-hidden="true"></i>
                    ${msg("Condition", { id: "policies.conditional.group.add-condition" })}
                </button>
            </div>
        </div>`;
    }

    //#endregion

    protected renderTargetSelect() {
        return html`<label class="target">
            ${msg("Showing values for", { id: "policies.conditional.target.label" })}
            <select
                class="pf-c-form-control"
                @change=${(ev: Event) => {
                    this.target = (ev.target as HTMLSelectElement).value || null;
                }}
            >
                <option value="" ?selected=${!this.target}>
                    ${msg("any object", { id: "policies.conditional.target.any" })}
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
        </label>`;
    }

    render() {
        if (!this.catalog) {
            return html`<ak-spinner></ak-spinner>`;
        }

        if (!this.#normalized) {
            this.tree.root = removeNotNodes(this.catalog, this.tree.root);
            this.#normalized = true;
        }

        const root = this.tree.root as GroupNode;

        this.#paths = collectNodePaths(root);
        this.#ownedErrors = assignErrors(this.errors, this.#paths.values());

        // Errors of the root group, and errors which don't belong to any node
        const rootErrors = [...this.nodeErrors(root), ...(this.#ownedErrors.get("") ?? [])];

        const add = (node: ConditionNode) => {
            root.children.push(node);
            this.changed();
        };

        return html`<div class="builder">
            <div class="toolbar">
                <div class="sentence">
                    <span>${msg("Pass when", { id: "policies.conditional.root.prefix" })}</span>
                    ${this.renderGroupOp(root)}
                    <span>
                        ${msg("of these are true", { id: "policies.conditional.group.suffix" })}
                    </span>
                </div>
                ${this.renderTargetSelect()}
            </div>
            ${this.renderErrors(rootErrors)}
            ${
                root.children.length
                    ? this.renderChildren(root)
                    : html`<p class="empty">
                          ${msg("Add a condition to get started.", {
                              id: "policies.conditional.empty",
                          })}
                      </p>`
            }
            <div class="add">
                <button
                    type="button"
                    class="pf-c-button pf-m-secondary pf-m-small"
                    @click=${() => add(newCondition())}
                >
                    <i class="fas fa-plus" aria-hidden="true"></i>
                    ${msg("Add condition", { id: "policies.conditional.add-condition" })}
                </button>
                <button
                    type="button"
                    class="pf-c-button pf-m-link pf-m-small"
                    @click=${() => add({ type: "group", op: "any", children: [newCondition()] })}
                >
                    <i class="fas fa-plus" aria-hidden="true"></i>
                    ${msg("Add group", { id: "policies.conditional.add-group" })}
                </button>
                <button
                    type="button"
                    class="pf-c-button pf-m-link pf-m-small"
                    @click=${() => add({ type: "policy", policy: "" })}
                >
                    <i class="fas fa-plus" aria-hidden="true"></i>
                    ${msg("Include another policy", { id: "policies.conditional.add-policy" })}
                </button>
            </div>
            ${
                root.children.length
                    ? html`<div class="summary">
                          ${msg(str`Reads as: ${describe(this.catalog, root)}`, {
                              id: "policies.conditional.summary",
                          })}
                      </div>`
                    : nothing
            }
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-condition-builder": AkConditionBuilder;
    }
}

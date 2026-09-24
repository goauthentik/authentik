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
    collectPaths,
    CompareNode,
    ConditionErrors,
    describe,
    describeAction,
    emptyActions,
    errorOwner,
    factsForScenario,
    filterPickerOptions,
    findSetter,
    findVariable,
    isAvailable,
    isTextual,
    newCondition,
    operandType,
    operatorChoiceId,
    operatorChoices,
    operatorsFor,
    objectLabelKey,
    ObjectLabels,
    PickerOption,
    POLICY_MODEL,
    pickerOptionId,
    pickerOptions,
    removeNotNodesFromActions,
    ValueType,
    variableCategory,
    variableType,
} from "#admin/policies/conditional/utils";

import {
    Application,
    ConditionCatalog,
    ConditionGroupNode,
    ConditionNode,
    ConditionOperand,
    ConditionOperatorName,
    ConditionParamKindEnum,
    ConditionPolicyNode,
    ConditionTypeKindEnum,
    ConditionVariableRef,
    CoreApi,
    Group,
    PoliciesApi,
    Policy,
    PolicyAction,
    PolicyActionIf,
    PolicyActions,
    PolicyActionSet,
    PolicyActionStop,
    Source,
    SourcesApi,
    User,
} from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { css, html, nothing, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

type GroupNode = ConditionGroupNode & { type: "group" };

type PolicyNode = ConditionPolicyNode & { type: "policy" };

type IfAction = PolicyActionIf & { type: "if" };

type SetAction = PolicyActionSet & { type: "set" };

type StopAction = PolicyActionStop & { type: "stop" };

/**
 * A type of action or condition which can be added
 */
interface BlockType<T> {
    icon: string;
    title: string;
    description: string;
    create: () => T;
}

const ACTION_TYPES: [string, BlockType<PolicyAction>[]][] = [
    [
        msg("Conditions", { id: "policies.actions.picker.conditions" }),
        [
            {
                icon: "fa-filter",
                title: msg("Check a value", { id: "policies.actions.type.check.title" }),
                description: msg("Stop and fail when a value doesn't match.", {
                    id: "policies.actions.type.check.description",
                }),
                create: () => ({ type: "condition", condition: newCondition() }),
            },
            {
                icon: "fa-layer-group",
                title: msg("Check several values", {
                    id: "policies.actions.type.check-group.title",
                }),
                description: msg("Stop and fail unless all, any or none of them match.", {
                    id: "policies.actions.type.check-group.description",
                }),
                create: () => ({
                    type: "condition",
                    condition: { type: "group", op: "all", children: [newCondition()] },
                }),
            },
            {
                icon: "fa-shield-alt",
                title: msg("Check another policy", {
                    id: "policies.actions.type.check-policy.title",
                }),
                description: msg("Stop and fail when another policy doesn't pass.", {
                    id: "policies.actions.type.check-policy.description",
                }),
                create: () => ({ type: "condition", condition: { type: "policy", policy: "" } }),
            },
        ],
    ],
    [
        msg("Building blocks", { id: "policies.actions.picker.blocks" }),
        [
            {
                icon: "fa-code-branch",
                title: msg("If, then, else", { id: "policies.actions.type.if.title" }),
                description: msg("Run different actions depending on a condition.", {
                    id: "policies.actions.type.if.description",
                }),
                create: () => ({
                    type: "if",
                    condition: newCondition(),
                    thenActions: [],
                    elseActions: [],
                }),
            },
            {
                icon: "fa-hand-paper",
                title: msg("Stop", { id: "policies.actions.type.stop.title" }),
                description: msg("Stop and pass or fail, optionally with a message.", {
                    id: "policies.actions.type.stop.description",
                }),
                create: () => ({ type: "stop", result: "fail" }),
            },
        ],
    ],
    [
        msg("Values", { id: "policies.actions.picker.values" }),
        [
            {
                icon: "fa-pen",
                title: msg("Set a value", { id: "policies.actions.type.set.title" }),
                description: msg(
                    "Set a value in the flow, for example a prompt field or the flow context.",
                    { id: "policies.actions.type.set.description" },
                ),
                create: () => ({
                    type: "set",
                    target: { key: "" },
                    value: { type: "literal", value: "" },
                }),
            },
        ],
    ],
];

const CONDITION_TYPES: BlockType<ConditionNode>[] = [
    {
        icon: "fa-filter",
        title: msg("Compare a value", { id: "policies.actions.condition.compare.title" }),
        description: msg("For example the user's email address or the client's country.", {
            id: "policies.actions.condition.compare.description",
        }),
        create: () => newCondition(),
    },
    {
        icon: "fa-layer-group",
        title: msg("Group", { id: "policies.actions.condition.group.title" }),
        description: msg("All, any or none of multiple conditions.", {
            id: "policies.actions.condition.group.description",
        }),
        create: () => ({ type: "group", op: "any", children: [newCondition()] }),
    },
    {
        icon: "fa-shield-alt",
        title: msg("Another policy", { id: "policies.actions.condition.policy.title" }),
        description: msg("Passes when another policy passes.", {
            id: "policies.actions.condition.policy.description",
        }),
        create: () => ({ type: "policy", policy: "" }),
    },
];

const GROUP_LABELS: Record<string, string> = {
    all: msg("All of these", { id: "policies.actions.group.all" }),
    any: msg("Any of these", { id: "policies.actions.group.any" }),
    none: msg("None of these", { id: "policies.actions.group.none" }),
};

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
 * Editor for the actions of a conditional policy, inspired by the Home Assistant automation
 * editor: actions and conditions are shown as cards, the selected card is edited in a side
 * panel.
 *
 * @fires input - When the actions are modified
 */
@customElement("ak-policy-action-builder")
export class AkPolicyActionBuilder extends AKControlElement<PolicyActions> {
    static styles = [
        PFButton,
        PFForm,
        PFFormControl,
        PFLabel,
        css`
            :host {
                display: block;
                container-type: inline-size;
            }
            .toolbar {
                display: flex;
                flex-wrap: wrap;
                justify-content: space-between;
                align-items: center;
                gap: var(--pf-global--spacer--sm);
                margin-bottom: var(--pf-global--spacer--md);
                color: var(--pf-global--Color--200);
            }
            .scenario {
                display: flex;
                flex-direction: column;
                align-items: flex-end;
                gap: var(--pf-global--spacer--xs);
                max-width: 28rem;
            }
            .scenario .help {
                text-align: right;
            }
            .toolbar label {
                display: flex;
                align-items: center;
                gap: var(--pf-global--spacer--sm);
                white-space: nowrap;
                font-size: var(--pf-global--FontSize--sm);
            }
            .layout {
                display: grid;
                grid-template-columns: minmax(0, 3fr) minmax(18rem, 2fr);
                gap: var(--pf-global--spacer--md);
                align-items: start;
            }
            @container (max-width: 52rem) {
                .layout {
                    grid-template-columns: minmax(0, 1fr);
                }
            }
            .list {
                display: flex;
                flex-direction: column;
                gap: var(--pf-global--spacer--sm);
            }
            .card {
                border: 1px solid var(--pf-global--BorderColor--100);
                border-radius: 8px;
                background: var(--pf-global--BackgroundColor--100);
            }
            .card.selected {
                border-color: var(--pf-global--primary-color--100);
                box-shadow: 0 0 0 1px var(--pf-global--primary-color--100);
            }
            .card.invalid {
                border-color: var(--pf-global--danger-color--100);
            }
            .card.disabled > .head {
                opacity: 0.55;
            }
            .head {
                position: relative;
                display: flex;
                align-items: center;
                gap: var(--pf-global--spacer--sm);
                padding: var(--pf-global--spacer--sm);
                cursor: pointer;
            }
            .icon {
                width: 2.25rem;
                height: 2.25rem;
                flex-shrink: 0;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                background: var(--pf-global--palette--blue-50);
                color: var(--pf-global--primary-color--100);
            }
            .icon.block {
                background: var(--pf-global--palette--purple-50);
                color: var(--pf-global--palette--purple-500);
            }
            .icon.value {
                background: var(--pf-global--palette--green-50);
                color: var(--pf-global--palette--green-500);
            }
            .icon.stop {
                background: var(--pf-global--palette--red-50);
                color: var(--pf-global--danger-color--100);
            }
            .title {
                flex: 1;
                min-width: 0;
            }
            .kind {
                font-size: var(--pf-global--FontSize--xs);
                color: var(--pf-global--Color--200);
            }
            .description {
                overflow-wrap: anywhere;
            }
            .badge {
                font-size: var(--pf-global--FontSize--xs);
                border-radius: 1rem;
                padding: 0 var(--pf-global--spacer--sm);
                background: var(--pf-global--BackgroundColor--200);
                color: var(--pf-global--Color--200);
            }
            .error-icon {
                color: var(--pf-global--danger-color--100);
            }
            .body {
                border-top: 1px solid var(--pf-global--BorderColor--100);
                padding: var(--pf-global--spacer--sm) var(--pf-global--spacer--sm)
                    var(--pf-global--spacer--sm) var(--pf-global--spacer--xl);
                display: flex;
                flex-direction: column;
                gap: var(--pf-global--spacer--sm);
                background: var(--pf-global--BackgroundColor--200);
                border-radius: 0 0 8px 8px;
            }
            .section-label {
                font-size: var(--pf-global--FontSize--xs);
                font-weight: var(--pf-global--FontWeight--bold);
                text-transform: uppercase;
                letter-spacing: 0.04em;
                color: var(--pf-global--Color--200);
            }
            .add {
                border: 1px dashed var(--pf-global--BorderColor--100);
                border-radius: 8px;
                background: none;
                padding: var(--pf-global--spacer--sm);
                color: var(--pf-global--primary-color--100);
                font: inherit;
                cursor: pointer;
                width: 100%;
            }
            .add.active {
                border-style: solid;
                border-color: var(--pf-global--primary-color--100);
            }
            .menu {
                position: absolute;
                right: 0;
                top: calc(100% - 4px);
                z-index: 10;
                min-width: 13rem;
                background: var(--pf-global--BackgroundColor--100);
                border: 1px solid var(--pf-global--BorderColor--100);
                box-shadow: var(--pf-global--BoxShadow--md);
                padding: var(--pf-global--spacer--xs) 0;
                cursor: default;
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
            .menu button:disabled {
                color: var(--pf-global--disabled-color--100);
                cursor: default;
            }
            .menu button.danger {
                color: var(--pf-global--danger-color--100);
            }
            .menu hr {
                border: none;
                border-top: 1px solid var(--pf-global--BorderColor--100);
                margin: var(--pf-global--spacer--xs) 0;
            }
            .menu .menu-icon {
                width: 1rem;
                text-align: center;
            }
            .panel {
                position: sticky;
                top: 0;
                border: 1px solid var(--pf-global--BorderColor--100);
                border-radius: 8px;
                background: var(--pf-global--BackgroundColor--100);
                padding: var(--pf-global--spacer--md);
                display: flex;
                flex-direction: column;
                gap: var(--pf-global--spacer--md);
            }
            .panel h3 {
                margin: 0;
                font-size: var(--pf-global--FontSize--lg);
            }
            .panel .subtitle {
                color: var(--pf-global--Color--200);
                font-size: var(--pf-global--FontSize--sm);
            }
            .field {
                display: flex;
                flex-direction: column;
                gap: var(--pf-global--spacer--xs);
            }
            .field > label,
            .field > .label {
                font-weight: var(--pf-global--FontWeight--bold);
                font-size: var(--pf-global--FontSize--sm);
            }
            .help {
                font-size: var(--pf-global--FontSize--xs);
                color: var(--pf-global--Color--200);
            }
            .inline {
                display: flex;
                flex-wrap: wrap;
                gap: var(--pf-global--spacer--sm);
                align-items: center;
            }
            .inline > * {
                flex: 1 1 8rem;
            }
            .segmented {
                display: inline-flex;
                border: 1px solid var(--pf-global--BorderColor--100);
                border-radius: 3px;
                overflow: hidden;
                align-self: flex-start;
            }
            .segmented button {
                background: none;
                border: none;
                border-right: 1px solid var(--pf-global--BorderColor--100);
                padding: var(--pf-global--spacer--xs) var(--pf-global--spacer--md);
                font: inherit;
                cursor: pointer;
            }
            .segmented button:last-child {
                border-right: none;
            }
            .segmented button.on {
                background: var(--pf-global--primary-color--100);
                color: var(--pf-global--Color--light-100);
            }
            .chips {
                display: flex;
                flex-wrap: wrap;
                gap: var(--pf-global--spacer--xs);
                align-items: center;
            }
            .chips input {
                width: 8rem;
                flex: 1 1 8rem;
            }
            .picker-item {
                display: flex;
                gap: var(--pf-global--spacer--sm);
                align-items: center;
                width: 100%;
                text-align: left;
                background: none;
                border: none;
                border-radius: 4px;
                padding: var(--pf-global--spacer--sm);
                font: inherit;
                color: inherit;
                cursor: pointer;
            }
            .picker-item:hover {
                background: var(--pf-global--BackgroundColor--200);
            }
            .picker-item .item-title {
                font-weight: var(--pf-global--FontWeight--bold);
            }
            .empty {
                color: var(--pf-global--Color--200);
                padding: var(--pf-global--spacer--sm) 0;
            }
            .warning {
                color: var(--pf-global--warning-color--200);
                font-size: var(--pf-global--FontSize--sm);
            }
            .check {
                display: flex;
                align-items: center;
                gap: var(--pf-global--spacer--sm);
            }
        `,
    ];

    @property({ type: String })
    public name = "actions";

    @property({ attribute: false })
    public catalog?: ConditionCatalog;

    /**
     * Initial value
     */
    @property({ attribute: false })
    public set value(value: PolicyActions | undefined) {
        this.tree = value ? (structuredClone(value) as PolicyActions) : emptyActions();
        this.#normalized = false;
        this.selected = null;
        this.adding = null;
    }

    public get value(): PolicyActions {
        return this.tree;
    }

    /**
     * Names of objects referenced by actions, keyed by `<model>:<pk>`, to show them instead of
     * their primary keys. Names of objects picked in the editor are added.
     */
    @property({ attribute: false })
    public set labels(value: ObjectLabels | undefined) {
        Object.assign(this.#labels, value);
    }

    public get labels(): ObjectLabels {
        return this.#labels;
    }

    #labels: ObjectLabels = {};

    /**
     * Validation errors returned by the API, keyed by the path of the item they belong to.
     */
    @property({ attribute: false })
    public errors: ConditionErrors = {};

    /**
     * Key of the scenario the policy is used in, to only offer values which are available
     * there.
     */
    @state()
    protected scenario: string | null = null;

    @state()
    protected tree: PolicyActions = emptyActions();

    /**
     * The action or condition being edited in the side panel.
     */
    @state()
    protected selected: PolicyAction | ConditionNode | null = null;

    /**
     * The list a new action or condition is being added to.
     */
    @state()
    protected adding: {
        list: PolicyAction[] | ConditionNode[];
        kind: "action" | "condition";
    } | null = null;

    @state()
    protected openMenu: object | null = null;

    #normalized = false;

    #paths = new Map<object, string>();

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

    public toJSON(): PolicyActions {
        return this.tree;
    }

    /**
     * Called when the actions were modified. When a single `item` was edited, only its errors
     * are cleared. Otherwise the structure changed, and as paths may have changed, all errors
     * are cleared.
     */
    protected changed(item?: object) {
        const path = item ? this.#paths.get(item) : undefined;

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

    protected errorsFor(...items: object[]): string[] {
        return items.flatMap((item) => {
            const path = this.#paths.get(item);

            return path === undefined ? [] : (this.#ownedErrors.get(path) ?? []);
        });
    }

    /**
     * Errors of an action, including errors of its condition which is edited with the action.
     */
    protected actionErrors(action: PolicyAction): string[] {
        if (action.type === "condition" || action.type === "if") {
            return this.errorsFor(action, action.condition);
        }

        return this.errorsFor(action);
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
        return factsForScenario(this.catalog, this.scenario);
    }

    protected select(item: PolicyAction | ConditionNode) {
        this.selected = item;
        this.adding = null;
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
            @ak-change=${(
                ev: CustomEvent<{ value: Application | Group | Source | User | null }>,
            ) => {
                const obj = ev.detail.value;
                const pk = lookup.value(obj);

                if (obj && pk) this.labels[objectLabelKey(model, pk)] = lookup.render(obj);

                onChange(pk);
            }}
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

    /**
     * Editor for a fixed value or another variable, of the type `expected`.
     */
    protected renderOperandEditor(
        operand: ConditionOperand | null | undefined,
        expected: ValueType,
        rangeType: ValueType | null,
        onChange: (operand: ConditionOperand) => void,
    ): TemplateResult {
        const isVariable = operand?.type === "variable";

        const source = html`<div class="segmented" role="group">
            <button
                type="button"
                class=${isVariable ? "" : "on"}
                @click=${() => onChange({ type: "literal", value: null })}
            >
                ${msg("Fixed value", { id: "policies.actions.operand.literal" })}
            </button>
            <button
                type="button"
                class=${isVariable ? "on" : ""}
                @click=${() => onChange({ type: "variable", variable: { key: "" } })}
            >
                ${msg("Another value", { id: "policies.actions.operand.variable" })}
            </button>
        </div>`;

        if (operand?.type === "variable") {
            const ref = operand.variable;

            const update = (variable: ConditionVariableRef) =>
                onChange({ type: "variable", variable });

            return html`${source} ${this.renderVariablePicker(ref, update)}
                <div class="inline">${this.renderVariableDetails(ref, update)}</div>`;
        }

        const current = operand?.type === "literal" ? operand.value : undefined;
        const setLiteral = (value: unknown) => onChange({ type: "literal", value });
        let editor: TemplateResult;

        if (rangeType) {
            const values = Array.isArray(current) ? current : [null, null];

            editor = html`<div class="inline">
                ${this.renderScalarInput(rangeType, values[0], (value) =>
                    setLiteral([value, values[1]]),
                )}
                <span>${msg("and", { id: "policies.conditional.value.range.separator" })}</span>
                ${this.renderScalarInput(rangeType, values[1], (value) =>
                    setLiteral([values[0], value]),
                )}
            </div>`;
        } else if (expected.kind === ConditionTypeKindEnum.List && expected.item) {
            editor = this.renderListInput(expected.item, current, setLiteral);
        } else {
            editor = this.renderScalarInput(expected, current, setLiteral);
        }

        return html`${source} ${editor}`;
    }

    //#endregion

    //#region Editors

    protected renderCompareEditor(node: CompareNode) {
        const type = variableType(this.catalog, node.variable);
        const choices = operatorChoices(this.catalog, type);
        const operator = this.catalog?.operators.find((op) => op.name === node.operator);
        const expected = operandType(operator, type);
        const variable = findVariable(this.catalog, node.variable.key);
        const selectedChoice = operatorChoiceId(node.operator, node.options?.negate);

        return html`<div class="field">
                <span class="label">${msg("Value", { id: "policies.actions.compare.value" })}</span>
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
                <div class="inline">
                    ${this.renderVariableDetails(node.variable, (ref) => {
                        node.variable = ref;
                        this.changed(node);
                    })}
                </div>
                ${variable ? html`<span class="help">${variable.description}</span>` : nothing}
                ${
                    variable && !isAvailable(variable, this.facts)
                        ? html`<span class="warning">
                              <i class="fas fa-exclamation-triangle" aria-hidden="true"></i>
                              ${msg("Not available for the selected object", {
                                  id: "policies.conditional.variable.unavailable",
                              })}
                          </span>`
                        : nothing
                }
            </div>
            <div class="field">
                <label for="operator">
                    ${msg("Comparison", { id: "policies.actions.compare.operator" })}
                </label>
                <select
                    id="operator"
                    class="pf-c-form-control"
                    ?disabled=${!type}
                    @change=${(ev: Event) => {
                        const choice = choices.find(
                            (c) => c.id === (ev.target as HTMLSelectElement).value,
                        );

                        if (!choice) return;

                        const previous = operandType(operator, type);

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
            </div>
            ${
                expected
                    ? html`<div class="field">
                          <span class="label">
                              ${msg("Compared with", { id: "policies.actions.compare.operand" })}
                          </span>
                          ${this.renderOperandEditor(
                              node.value,
                              expected,
                              operator?.operand === "range" ? type : null,
                              (operand) => {
                                  node.value = operand;
                                  this.changed(node);
                              },
                          )}
                      </div>`
                    : nothing
            }
            ${
                isTextual(type)
                    ? html`<label class="check">
                          <input
                              type="checkbox"
                              .checked=${node.options?.caseSensitive === false}
                              @change=${(ev: Event) => {
                                  node.options = {
                                      ...node.options,
                                      caseSensitive: !(ev.target as HTMLInputElement).checked,
                                  };

                                  this.changed(node);
                              }}
                          />
                          ${msg("Ignore upper/lower case", {
                              id: "policies.conditional.menu.ignore-case",
                          })}
                      </label>`
                    : nothing
            }`;
    }

    protected renderGroupEditor(node: GroupNode) {
        return html`<div class="field">
            <span class="label">${msg("Passes when", { id: "policies.actions.group.label" })}</span>
            <div class="segmented" role="group">
                ${(["all", "any", "none"] as const).map(
                    (op) =>
                        html`<button
                            type="button"
                            class=${node.op === op ? "on" : ""}
                            @click=${() => {
                                node.op = op;
                                this.changed(node);
                            }}
                        >
                            ${GROUP_LABELS[op]}
                        </button>`,
                )}
            </div>
            <span class="help">
                ${msg("Add, edit and remove the conditions of this group in the list.", {
                    id: "policies.actions.group.help",
                })}
            </span>
        </div>`;
    }

    protected renderPolicyEditor(node: PolicyNode) {
        return html`<div class="field">
            <span class="label">${msg("Policy", { id: "policies.actions.policy.label" })}</span>
            <ak-search-select
                .fetchObjects=${async (search?: string): Promise<Policy[]> =>
                    (await aki(PoliciesApi).policiesAllList({ search, ordering: "name" })).results}
                .renderElement=${(policy: Policy) => policy.name}
                .value=${(policy: Policy | null) => policy?.pk}
                .selected=${(policy: Policy) => policy.pk === node.policy}
                @ak-change=${(ev: CustomEvent<{ value: Policy | null }>) => {
                    const policy = ev.detail.value;

                    if (policy) this.labels[objectLabelKey(POLICY_MODEL, policy.pk)] = policy.name;

                    node.policy = policy?.pk ?? "";
                    this.changed(node);
                }}
            ></ak-search-select>
            <span class="help">
                ${msg("Passes when the selected policy passes.", {
                    id: "policies.actions.policy.help",
                })}
            </span>
        </div>`;
    }

    protected renderConditionEditor(node: ConditionNode) {
        switch (node.type) {
            case "compare":
                return this.renderCompareEditor(node as CompareNode);
            case "group":
                return this.renderGroupEditor(node as GroupNode);
            case "policy":
                return this.renderPolicyEditor(node as PolicyNode);
            default:
                return nothing;
        }
    }

    protected renderSetEditor(action: SetAction) {
        const setter = findSetter(this.catalog, action.target.key);
        const facts = this.facts;

        const setters = (this.catalog?.setters ?? []).filter(
            (candidate) => isAvailable(candidate, facts) || candidate.key === action.target.key,
        );

        return html`<div class="field">
                <label for="setter">${msg("Set", { id: "policies.actions.set.target" })}</label>
                <select
                    id="setter"
                    class="pf-c-form-control"
                    @change=${(ev: Event) => {
                        action.target = { key: (ev.target as HTMLSelectElement).value };
                        action.value = { type: "literal", value: "" };
                        this.changed(action);
                    }}
                >
                    <option value="" ?selected=${!setter} disabled>
                        ${msg("Choose what to set...", { id: "policies.actions.set.placeholder" })}
                    </option>
                    ${setters.map(
                        (candidate) =>
                            html`<option
                                value=${candidate.key}
                                ?selected=${candidate.key === action.target.key}
                            >
                                ${candidate.label}
                            </option>`,
                    )}
                </select>
                ${setter ? html`<span class="help">${setter.description}</span>` : nothing}
            </div>
            ${
                setter && setter.param !== ConditionParamKindEnum.None
                    ? html`<div class="field">
                          <label for="setter-key">
                              ${msg("Key", { id: "policies.actions.set.key" })}
                          </label>
                          <input
                              id="setter-key"
                              type="text"
                              class="pf-c-form-control"
                              .value=${action.target.param ?? ""}
                              @input=${(ev: InputEvent) => {
                                  action.target = {
                                      ...action.target,
                                      param: (ev.target as HTMLInputElement).value,
                                  };

                                  this.changed(action);
                              }}
                          />
                      </div>`
                    : nothing
            }
            ${
                setter
                    ? html`<div class="field">
                          <span class="label"
                              >${msg("To", { id: "policies.actions.set.value" })}</span
                          >
                          ${this.renderOperandEditor(
                              action.value,
                              setter.type.kind === ConditionTypeKindEnum.Any
                                  ? { kind: ConditionTypeKindEnum.String }
                                  : setter.type,
                              null,
                              (operand) => {
                                  action.value = operand;
                                  this.changed(action);
                              },
                          )}
                      </div>`
                    : nothing
            }`;
    }

    protected renderStopEditor(action: StopAction) {
        return html`<div class="field">
                <span class="label">${msg("Result", { id: "policies.actions.stop.result" })}</span>
                <div class="segmented" role="group">
                    <button
                        type="button"
                        class=${action.result === "pass" ? "on" : ""}
                        @click=${() => {
                            action.result = "pass";
                            this.changed(action);
                        }}
                    >
                        ${msg("Pass", { id: "policies.actions.stop.pass" })}
                    </button>
                    <button
                        type="button"
                        class=${action.result === "fail" ? "on" : ""}
                        @click=${() => {
                            action.result = "fail";
                            this.changed(action);
                        }}
                    >
                        ${msg("Fail", { id: "policies.actions.stop.fail" })}
                    </button>
                </div>
            </div>
            <div class="field">
                <label for="stop-message">
                    ${msg("Message", { id: "policies.actions.stop.message" })}
                </label>
                <input
                    id="stop-message"
                    type="text"
                    class="pf-c-form-control"
                    .value=${action.message ?? ""}
                    @input=${(ev: InputEvent) => {
                        action.message = (ev.target as HTMLInputElement).value || null;
                        this.changed(action);
                    }}
                />
                <span class="help">
                    ${msg("Shown to the user. Leave empty to use the policy's failure message.", {
                        id: "policies.actions.stop.message.help",
                    })}
                </span>
            </div>`;
    }

    protected renderActionEditor(action: PolicyAction) {
        let editor: TemplateResult | typeof nothing;

        switch (action.type) {
            case "condition":
                editor = this.renderConditionEditor(action.condition);
                break;
            case "if":
                editor = html`${this.renderConditionEditor(action.condition)}
                    <span class="help">
                        ${msg(
                            "When the condition passes, the “then” actions run, otherwise the “else” actions.",
                            { id: "policies.actions.if.help" },
                        )}
                    </span>`;
                break;
            case "set":
                editor = this.renderSetEditor(action as SetAction);
                break;
            case "stop":
                editor = this.renderStopEditor(action as StopAction);
                break;
            default:
                editor = nothing;
        }

        return html`${editor}
            <label class="check">
                <input
                    type="checkbox"
                    .checked=${action.enabled !== false}
                    @change=${(ev: Event) => {
                        action.enabled = (ev.target as HTMLInputElement).checked;
                        this.changed(action);
                    }}
                />
                ${msg("Enabled", { id: "policies.actions.enabled" })}
            </label>`;
    }

    //#endregion

    //#region Side panel

    protected renderPicker() {
        if (!this.adding) return nothing;

        const { list, kind } = this.adding;

        const add = (item: PolicyAction | ConditionNode) => {
            (list as (PolicyAction | ConditionNode)[]).push(item);
            this.changed();
            this.select(item);
        };

        const item = <T>(type: BlockType<T>, iconClass = "") =>
            html`<button
                type="button"
                class="picker-item"
                @click=${() => add(type.create() as PolicyAction)}
            >
                <span class="icon ${iconClass}"
                    ><i class="fas ${type.icon}" aria-hidden="true"></i
                ></span>
                <span>
                    <span class="item-title">${type.title}</span><br />
                    <span class="help">${type.description}</span>
                </span>
            </button>`;

        const iconClasses: Record<string, string> = {
            "fa-code-branch": "block",
            "fa-hand-paper": "stop",
            "fa-pen": "value",
        };

        return html`<aside class="panel">
            <div>
                <h3>
                    ${
                        kind === "action"
                            ? msg("Add action", { id: "policies.actions.picker.add-action" })
                            : msg("Add condition", { id: "policies.actions.picker.add-condition" })
                    }
                </h3>
            </div>
            ${
                kind === "action"
                    ? ACTION_TYPES.map(
                          ([category, types]) =>
                              html`<div class="field">
                                  <span class="section-label">${category}</span>
                                  ${types.map((type) => item(type, iconClasses[type.icon] ?? ""))}
                              </div>`,
                      )
                    : CONDITION_TYPES.map((type) => item(type))
            }
            <button
                type="button"
                class="pf-c-button pf-m-link"
                @click=${() => {
                    this.adding = null;
                }}
            >
                ${msg("Cancel", { id: "policies.actions.picker.cancel" })}
            </button>
        </aside>`;
    }

    protected renderPanel() {
        if (this.adding) return this.renderPicker();

        const item = this.selected;

        if (!item || !this.#paths.has(item)) {
            return html`<aside class="panel">
                <p class="empty">
                    ${msg("Select an action to edit it, or add a new one.", {
                        id: "policies.actions.panel.empty",
                    })}
                </p>
            </aside>`;
        }

        const isAction = ["condition", "if", "set", "stop"].includes(item.type);
        const errors = isAction ? this.actionErrors(item as PolicyAction) : this.errorsFor(item);
        const [kind] = this.describeKind(item);

        return html`<aside class="panel">
            <div>
                <h3>${kind}</h3>
                <div class="subtitle">${this.describeItem(item)}</div>
            </div>
            ${this.renderErrors(errors)}
            ${
                isAction
                    ? this.renderActionEditor(item as PolicyAction)
                    : this.renderConditionEditor(item as ConditionNode)
            }
        </aside>`;
    }

    //#endregion

    //#region Cards

    /**
     * Label of the kind of an action or condition, and the class of its icon.
     */
    protected describeKind(item: PolicyAction | ConditionNode): [string, string, string] {
        switch (item.type) {
            case "condition":
                return [msg("Check", { id: "policies.actions.kind.check" }), "fa-filter", ""];
            case "if":
                return [
                    msg("If, then, else", { id: "policies.actions.kind.if" }),
                    "fa-code-branch",
                    "block",
                ];
            case "set":
                return [msg("Set a value", { id: "policies.actions.kind.set" }), "fa-pen", "value"];
            case "stop":
                return [msg("Stop", { id: "policies.actions.kind.stop" }), "fa-hand-paper", "stop"];
            case "group":
                return [msg("Group", { id: "policies.actions.kind.group" }), "fa-layer-group", ""];
            case "policy":
                return [msg("Policy", { id: "policies.actions.kind.policy" }), "fa-shield-alt", ""];
            case "compare": {
                const variable = findVariable(this.catalog, (item as CompareNode).variable.key);

                return [
                    variable
                        ? variableCategory(variable)
                        : msg("Compare", { id: "policies.actions.kind.compare" }),
                    "fa-filter",
                    "",
                ];
            }
            default:
                return ["", "fa-question", ""];
        }
    }

    protected describeItem(item: PolicyAction | ConditionNode): string {
        if (item.type === "group") return GROUP_LABELS[(item as GroupNode).op];

        if (["condition", "if", "set", "stop"].includes(item.type)) {
            const action = item as PolicyAction;

            if (
                (action.type === "condition" || action.type === "if") &&
                action.condition.type === "group"
            ) {
                const label = GROUP_LABELS[action.condition.op];

                return action.type === "if" ? `If ${label.toLowerCase()}` : label;
            }

            return describeAction(this.catalog, action, this.labels);
        }

        return describe(this.catalog, item as ConditionNode, this.labels);
    }

    protected renderMenu(item: object, entries: [string, string, () => void, boolean?][]) {
        return html`<button
                type="button"
                class="pf-c-button pf-m-plain"
                aria-label=${msg("Actions", { id: "policies.conditional.menu.aria-label" })}
                aria-expanded=${this.openMenu === item ? "true" : "false"}
                @click=${(ev: Event) => {
                    ev.stopPropagation();
                    this.openMenu = this.openMenu === item ? null : item;
                }}
            >
                <i class="fas fa-ellipsis-v" aria-hidden="true"></i>
            </button>
            ${
                this.openMenu === item
                    ? html`<div
                          class="menu"
                          role="menu"
                          @click=${(ev: Event) => ev.stopPropagation()}
                      >
                          ${entries.map(([icon, label, action, disabled]) =>
                              icon === "-"
                                  ? html`<hr />`
                                  : html`<button
                                        type="button"
                                        role="menuitem"
                                        class=${icon === "fa-trash" ? "danger" : ""}
                                        ?disabled=${disabled}
                                        @click=${() => action()}
                                    >
                                        <span class="menu-icon">
                                            <i class="fas ${icon}" aria-hidden="true"></i>
                                        </span>
                                        ${label}
                                    </button>`,
                          )}
                      </div>`
                    : nothing
            }`;
    }

    protected renderCard(
        item: PolicyAction | ConditionNode,
        errors: string[],
        menu: TemplateResult,
        body: TemplateResult | typeof nothing = nothing,
    ) {
        const [kind, icon, iconClass] = this.describeKind(item);
        const disabled = "enabled" in item && item.enabled === false;

        return html`<div
            class="card ${this.selected === item ? "selected" : ""} ${
                errors.length ? "invalid" : ""
            } ${disabled ? "disabled" : ""}"
        >
            <div
                class="head"
                role="button"
                tabindex="0"
                @click=${() => this.select(item)}
                @keydown=${(ev: KeyboardEvent) => {
                    if (ev.key === "Enter") this.select(item);
                }}
            >
                <span class="icon ${iconClass}"
                    ><i class="fas ${icon}" aria-hidden="true"></i
                ></span>
                <div class="title">
                    <div class="kind">${kind}</div>
                    <div class="description">${this.describeItem(item)}</div>
                </div>
                ${
                    errors.length
                        ? html`<i
                              class="fas fa-exclamation-circle error-icon"
                              title=${errors.join("\n")}
                              aria-label=${msg("Has errors", { id: "policies.actions.card.errors" })}
                          ></i>`
                        : nothing
                }
                ${disabled ? html`<span class="badge">${msg("Disabled", { id: "policies.actions.card.disabled" })}</span>` : nothing}
                <div @click=${(ev: Event) => ev.stopPropagation()}>${menu}</div>
            </div>
            ${body}
        </div>`;
    }

    protected renderAddButton(
        list: PolicyAction[] | ConditionNode[],
        kind: "action" | "condition",
    ) {
        const active = this.adding?.list === list;

        return html`<button
            type="button"
            class="add ${active ? "active" : ""}"
            @click=${() => {
                this.adding = { list, kind };
                this.selected = null;
            }}
        >
            <i class="fas fa-plus" aria-hidden="true"></i>
            ${
                kind === "action"
                    ? msg("Add action", { id: "policies.actions.add-action" })
                    : msg("Add condition", { id: "policies.actions.add-condition" })
            }
        </button>`;
    }

    /**
     * Cards of the conditions within a group.
     */
    protected renderConditionCards(group: GroupNode): TemplateResult {
        return html`${group.children.map((child, index) => {
            const menu = this.renderMenu(child, [
                [
                    "fa-object-group",
                    msg("Wrap in group", { id: "policies.conditional.menu.wrap" }),
                    () => {
                        const wrapped: ConditionNode = {
                            type: "group",
                            op: "any",
                            children: [child],
                        };

                        group.children[index] = wrapped;
                        this.changed();
                    },
                ],
                ...(child.type === "group"
                    ? ([
                          [
                              "fa-object-ungroup",
                              msg("Ungroup", { id: "policies.conditional.menu.ungroup" }),
                              () => {
                                  group.children.splice(index, 1, ...(child as GroupNode).children);
                                  this.changed();
                              },
                          ],
                      ] as [string, string, () => void][])
                    : []),
                [
                    "fa-copy",
                    msg("Duplicate", { id: "policies.conditional.menu.duplicate" }),
                    () => {
                        group.children.splice(index + 1, 0, structuredClone(child));
                        this.changed();
                    },
                ],
                ["-", "", () => undefined],
                [
                    "fa-trash",
                    msg("Delete", { id: "policies.conditional.menu.delete" }),
                    () => {
                        group.children.splice(index, 1);

                        if (this.selected === child) this.selected = null;
                        this.changed();
                    },
                ],
            ]);

            const body =
                child.type === "group" ? this.renderGroupBody(child as GroupNode) : nothing;

            return this.renderCard(child, this.errorsFor(child), menu, body);
        })}`;
    }

    protected renderGroupBody(group: GroupNode) {
        return html`<div class="body">
            ${this.renderConditionCards(group)} ${this.renderAddButton(group.children, "condition")}
        </div>`;
    }

    protected renderActionCards(list: PolicyAction[]): TemplateResult {
        return html`${list.map((action, index) => {
            const menu = this.renderMenu(action, [
                [
                    "fa-arrow-up",
                    msg("Move up", { id: "policies.actions.menu.up" }),
                    () => {
                        list.splice(index - 1, 0, ...list.splice(index, 1));
                        this.changed();
                    },
                    index === 0,
                ],
                [
                    "fa-arrow-down",
                    msg("Move down", { id: "policies.actions.menu.down" }),
                    () => {
                        list.splice(index + 1, 0, ...list.splice(index, 1));
                        this.changed();
                    },
                    index === list.length - 1,
                ],
                [
                    "fa-copy",
                    msg("Duplicate", { id: "policies.conditional.menu.duplicate" }),
                    () => {
                        list.splice(index + 1, 0, structuredClone(action));
                        this.changed();
                    },
                ],
                [
                    action.enabled === false ? "fa-toggle-on" : "fa-toggle-off",
                    action.enabled === false
                        ? msg("Enable", { id: "policies.actions.menu.enable" })
                        : msg("Disable", { id: "policies.actions.menu.disable" }),
                    () => {
                        action.enabled = action.enabled === false;
                        this.changed(action);
                    },
                ],
                ["-", "", () => undefined],
                [
                    "fa-trash",
                    msg("Delete", { id: "policies.conditional.menu.delete" }),
                    () => {
                        list.splice(index, 1);

                        if (this.selected === action) this.selected = null;
                        this.changed();
                    },
                ],
            ]);

            return this.renderCard(
                action,
                this.actionErrors(action),
                menu,
                this.renderActionBody(action),
            );
        })}`;
    }

    protected renderActionBody(action: PolicyAction): TemplateResult | typeof nothing {
        if (action.type === "condition") {
            return action.condition.type === "group"
                ? this.renderGroupBody(action.condition as GroupNode)
                : nothing;
        }

        if (action.type !== "if") return nothing;

        const ifAction = action as IfAction;

        ifAction.thenActions ??= [];
        ifAction.elseActions ??= [];

        return html`<div class="body">
            ${
                ifAction.condition.type === "group"
                    ? html`<span class="section-label">
                              ${msg("If", { id: "policies.actions.if.condition" })}
                          </span>
                          ${this.renderConditionCards(ifAction.condition as GroupNode)}
                          ${this.renderAddButton((ifAction.condition as GroupNode).children, "condition")}`
                    : nothing
            }
            <span class="section-label">${msg("Then", { id: "policies.actions.if.then" })}</span>
            ${this.renderActionCards(ifAction.thenActions)}
            ${this.renderAddButton(ifAction.thenActions, "action")}
            <span class="section-label">${msg("Else", { id: "policies.actions.if.else" })}</span>
            ${this.renderActionCards(ifAction.elseActions)}
            ${this.renderAddButton(ifAction.elseActions, "action")}
        </div>`;
    }

    //#endregion

    protected renderScenarioSelect() {
        const selected = this.catalog?.scenarios.find((scenario) => scenario.key === this.scenario);

        return html`<div class="scenario">
            <label>
                ${msg("Used for", { id: "policies.actions.scenario.label" })}
                <select
                    class="pf-c-form-control"
                    @change=${(ev: Event) => {
                        this.scenario = (ev.target as HTMLSelectElement).value || null;
                    }}
                >
                    <option value="" ?selected=${!this.scenario}>
                        ${msg("Any scenario (show all values)", {
                            id: "policies.actions.scenario.any",
                        })}
                    </option>
                    ${(this.catalog?.scenarios ?? []).map(
                        (scenario) =>
                            html`<option
                                value=${scenario.key}
                                ?selected=${scenario.key === this.scenario}
                            >
                                ${scenario.label}
                            </option>`,
                    )}
                </select>
            </label>
            <span class="help">
                ${
                    selected
                        ? selected.description
                        : msg(
                              "Choose where the policy is used to only show values available there.",
                              {
                                  id: "policies.actions.scenario.help",
                              },
                          )
                }
            </span>
        </div>`;
    }

    render() {
        if (!this.catalog) {
            return html`<ak-spinner></ak-spinner>`;
        }

        if (!this.#normalized) {
            this.tree.actions = removeNotNodesFromActions(this.catalog, this.tree.actions);
            this.#normalized = true;
        }

        const { actions } = this.tree;

        this.#paths = collectPaths(actions);
        this.#ownedErrors = assignErrors(this.errors, this.#paths.values());

        // Errors which don't belong to a specific action
        const generalErrors = [
            ...(this.#ownedErrors.get("actions") ?? []),
            ...(this.#ownedErrors.get("") ?? []),
        ];

        return html`<div class="toolbar">
                <span>
                    ${msg(
                        "Actions run from top to bottom. The policy passes when all actions complete.",
                        { id: "policies.actions.help" },
                    )}
                </span>
                ${this.renderScenarioSelect()}
            </div>
            ${this.renderErrors(generalErrors)}
            <div class="layout">
                <div class="list">
                    ${
                        actions.length
                            ? this.renderActionCards(actions)
                            : html`<p class="empty">
                                  ${msg("No actions yet.", { id: "policies.actions.empty" })}
                              </p>`
                    }
                    ${this.renderAddButton(actions, "action")}
                </div>
                ${this.renderPanel()}
            </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-policy-action-builder": AkPolicyActionBuilder;
    }
}

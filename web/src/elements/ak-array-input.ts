import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";

import { FormAssociatedElement, isFormField } from "#elements/forms/form-associated-element";
import { SettlingFormField } from "#elements/forms/settle-form-fields";
import { SlottedTemplateResult, type Spread } from "#elements/types";
import { randomId } from "#elements/utils/randomId";

import { spread } from "@open-wc/lit-helpers";
import type { Jsonifiable } from "type-fest";

import { msg } from "@lit/localize";
import { css, html, nothing, PropertyValues, ReactiveElement } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { repeat } from "lit/directives/repeat.js";

export type InputCell<T> = (el: T, idx: number) => SlottedTemplateResult | typeof nothing;

export interface IArrayInput<T> {
    row: InputCell<T>;
    newItem: () => T;
    items: T[];
    validate?: boolean;
    validator?: (_: T[]) => boolean;
}

interface Row<T> {
    key: string;
    item: T;
}

/**
 * A row element rendered by {@linkcode ArrayInput.row}.
 */
interface RowElement<T> extends HTMLElement {
    toJSON(): T;
    valid?: boolean;
}

/**
 * Two empty lists are the same list. Hosts often pass `items ?? []`, a new array on every render.
 */
function itemsChanged(nextItems: unknown[] | undefined, previousItems: unknown[] | undefined) {
    if (!nextItems?.length && !previousItems?.length) return false;

    return nextItems !== previousItems;
}

/**
 * An editable list of rows, each rendered by {@linkcode ArrayInput.row}.
 *
 * `items` is the list provided by the host. Assigning a different array replaces the rows.
 * Re-assigning the same array keeps the user's edits. A form reset restores `items`.
 *
 * @fires change - The user edited, added, or removed a row.
 */
@customElement("ak-array-input")
export class ArrayInput<T>
    extends FormAssociatedElement<string, Jsonifiable>
    implements IArrayInput<T>, SettlingFormField
{
    static styles = [
        PFButton,
        PFInputGroup,
        PFFormControl,
        css`
            select.pf-c-form-control {
                width: 100px;
            }
            .pf-c-input-group {
                padding-bottom: 0;
            }
            .ak-plus-button {
                display: flex;
                justify-content: flex-end;
                flex-direction: row;
            }
            .ak-input-group {
                display: flex;
                flex-direction: row;
                flex-wrap: nowrap;
            }
        `,
    ];

    //#region Properties

    /**
     * Check each row's `valid` and the {@linkcode validator} before the form submits.
     */
    @property({ type: Boolean })
    public validate = false;

    @property({ attribute: false })
    public validator?: (_: T[]) => boolean;

    @property({ attribute: false })
    public row!: InputCell<T>;

    @property({ attribute: false })
    public newItem!: () => T;

    @property({ attribute: false, hasChanged: itemsChanged })
    public items: T[] = [];

    //#endregion

    //#region State

    @state()
    protected rows: Row<T>[] = [];

    //#endregion

    //#region Lifecycle

    protected override willUpdate(changedProperties: PropertyValues<this>): void {
        super.willUpdate(changedProperties);

        if (changedProperties.has("items")) {
            this.#resetRows();
        }
    }

    #rowsUpdated: Promise<void> = Promise.resolve();

    protected override updated(changedProperties: PropertyValues<this>): void {
        super.updated(changedProperties);

        this.#rowsUpdated = Promise.all(
            this.#rowElements().map((element) =>
                element instanceof ReactiveElement ? element.updateComplete : true,
            ),
        ).then(() => this.#syncValidity());
    }

    protected override async getUpdateComplete(): Promise<boolean> {
        const result = await super.getUpdateComplete();

        await this.#rowsUpdated;

        return result;
    }

    /**
     * Resolves once the rows have rendered and the form value reflects them.
     */
    public get settled(): Promise<void> {
        return this.updateComplete.then(() => undefined);
    }

    public formResetCallback(): void {
        this.#resetRows();
    }

    public formStateRestoreCallback(state: string): void {
        this.rows = (JSON.parse(state) as T[]).map((item) => ({ key: randomId(), item }));
    }

    //#endregion

    //#region Value

    public toJSON(): T[] & Jsonifiable {
        return this.rows.map(({ item }) => item) as T[] & Jsonifiable;
    }

    #resetRows(): void {
        this.rows = (this.items ?? []).map((item) => ({ key: randomId(), item }));
    }

    #rowElements(): RowElement<T>[] {
        return Array.from(
            this.renderRoot.querySelectorAll<RowElement<T>>(".ak-input-group > [name]"),
        );
    }

    #syncValidity(): void {
        const values = this.toJSON();
        const rowElements = this.#rowElements();

        this.internals.setFormValue(JSON.stringify(values));

        let message: string | undefined;
        let anchor: HTMLElement | undefined;
        const flags: ValidityStateFlags = {};

        const invalidRow = this.validate
            ? rowElements.find((element) => element.valid === false)
            : undefined;

        if (this.validate && (invalidRow || (this.validator && !this.validator(values)))) {
            message = msg("One or more entries are invalid.", {
                id: "array-input.validation.invalid-entry",
            });

            flags.customError = true;
            anchor = invalidRow ?? rowElements[0];
        } else if (this.required && !values.length) {
            message = msg("This field is required.");
            flags.valueMissing = true;
            anchor = this.renderRoot.querySelector<HTMLElement>("button.pf-m-link") ?? undefined;
        }

        this.internals.setValidity(flags, message, anchor);
    }

    #dispatchChange(): void {
        this.dispatchEvent(new Event("change", { composed: true, bubbles: true }));
    }

    //#endregion

    //#region Event Listeners

    #rowChanged(key: string, event: Event): void {
        event.stopPropagation();

        if (!isFormField(event.target as object)) return;

        const item = (event.target as RowElement<T>).toJSON();

        this.rows = this.rows.map((row) => (row.key === key ? { key, item } : row));
        this.#dispatchChange();
    }

    #addRow = async (): Promise<void> => {
        this.rows = [...this.rows, { key: randomId(), item: this.newItem() }];
        this.#dispatchChange();

        await this.updateComplete;

        this.#rowElements().at(-1)?.focus();
    };

    #removeRow(key: string): void {
        this.rows = this.rows.filter((row) => row.key !== key);
        this.#dispatchChange();
    }

    //#endregion

    //#region Rendering

    render() {
        return html`<div class="pf-l-stack">
            ${repeat(
                this.rows,
                (row) => row.key,
                (row, idx) =>
                    html`<div
                        class="ak-input-group"
                        @change=${(event: Event) => this.#rowChanged(row.key, event)}
                    >
                        ${this.row(row.item, idx)}
                        <button
                            class="pf-c-button pf-m-control"
                            type="button"
                            aria-label=${msg("Remove entry", { id: "array-input.remove.aria-label" })}
                            @click=${() => this.#removeRow(row.key)}
                        >
                            <i class="fas fa-minus" aria-hidden="true"></i>
                        </button>
                    </div>`,
            )}
            <button class="pf-c-button pf-m-link" type="button" @click=${this.#addRow}>
                <span class="pf-c-button__icon pf-m-start">
                    <i class="fas fa-plus" aria-hidden="true"></i
                ></span>
                ${msg("Add entry")}
            </button>
        </div>`;
    }

    //#endregion
}

export function akArrayInput<T>(properties: IArrayInput<T>) {
    return html`<ak-array-input ${spread(properties as unknown as Spread)}></ak-array-input>`;
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-array-input": ArrayInput<unknown>;
    }
}

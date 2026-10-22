import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";

import { AKControlElement } from "#elements/ControlElement";
import { SlottedTemplateResult, type Spread } from "#elements/types";
import { randomId } from "#elements/utils/randomId";

import { spread } from "@open-wc/lit-helpers";

import { msg } from "@lit/localize";
import { css, html, nothing } from "lit";
import { customElement, property, queryAll } from "lit/decorators.js";
import { repeat } from "lit/directives/repeat.js";

export type InputCell<T> = (el: T, idx: number) => SlottedTemplateResult | typeof nothing;

export interface IArrayInput<T> {
    row: InputCell<T>;
    newItem: () => T;
    items: T[];
    validate?: boolean;
    validator?: (_: T[]) => boolean;
}

type Keyed<T> = { key: string; item: T };

@customElement("ak-array-input")
export class ArrayInput<T> extends AKControlElement<T[]> implements IArrayInput<T> {
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

    @property({ type: String })
    public name: string | null = null;

    @property({ type: Boolean })
    public validate = false;

    @property({ type: Object, attribute: false })
    public validator?: (_: T[]) => boolean;

    @property({ type: Array, attribute: false })
    public row!: InputCell<T>;

    @property({ type: Object, attribute: false })
    public newItem!: () => T;

    #items: Keyed<T>[] = [];

    /**
     * The last list the parent assigned, serialized. Lit re-assigns it on every parent render.
     */
    #assignedItems: string | null = null;

    // This magic creates a semi-reliable key on which Lit's `repeat` directive can control its
    // interaction. Without it, we get undefined behavior in the re-rendering of the array.
    @property({ type: Array, attribute: false })
    public set items(nextItems: T[]) {
        const assignedItems = JSON.stringify(nextItems);

        if (assignedItems === this.#assignedItems) return;

        this.#assignedItems = assignedItems;

        const previousKeys = new Map<string, string[]>();

        for (const { item, key } of this.#items) {
            const serialized = JSON.stringify(item);
            previousKeys.set(serialized, [...(previousKeys.get(serialized) ?? []), key]);
        }

        this.#items = nextItems.map((item) => ({
            item,
            key: previousKeys.get(JSON.stringify(item))?.shift() ?? randomId(),
        }));
    }

    get items() {
        return this.#items.map(({ item }) => item);
    }

    @queryAll("div.ak-input-group")
    protected inputGroups?: HTMLDivElement[];

    public toJSON(): T[] {
        if (!this.inputGroups) {
            throw new Error("Could not find input group collection in ak-array-input");
        }

        return this.items;
    }

    get valid() {
        if (!this.validate) {
            return true;
        }

        const oneIsValid = (g: HTMLDivElement) =>
            g.querySelector<HTMLInputElement & AKControlElement<T>>("[name]")?.valid ?? true;

        const allAreValid = Array.from(this.inputGroups ?? []).every(oneIsValid);

        return allAreValid && (this.validator ? this.validator(this.items) : true);
    }

    protected getNamedElements(): (HTMLInputElement & AKControlElement<T>)[] {
        return Array.from(this.inputGroups ?? []).map((group) =>
            group.querySelector<HTMLInputElement & AKControlElement<T>>("[name]")!,
        );
    }

    protected itemsFromDOM(): T[] {
        return Array.from(this.inputGroups ?? [])
            .map((group) => {
                return (
                    group
                        .querySelector<HTMLInputElement & AKControlElement<T>>("[name]")
                        ?.toJSON() ?? null
                );
            })
            .filter((i) => i !== null);
    }

    protected dispatchChangeEvent() {
        this.dispatchEvent(new Event("change", { composed: true, bubbles: true }));
    }

    /**
     * Read the rows' current values and keep their keys.
     */
    #syncFromDOM(): Keyed<T>[] {
        const values = this.itemsFromDOM();

        return this.#items.map((entry, idx) => ({ ...entry, item: values[idx] ?? entry.item }));
    }

    #setKeyedItems(nextItems: Keyed<T>[]) {
        const previousItems = this.items;
        this.#items = nextItems;
        this.requestUpdate("items", previousItems);
    }

    protected changeListener = () => {
        this.#setKeyedItems(this.#syncFromDOM());
        this.dispatchChangeEvent();
    };

    protected addNewGroup = () => {
        this.#setKeyedItems([...this.#syncFromDOM(), { key: randomId(), item: this.newItem() }]);
        this.dispatchChangeEvent();

        requestAnimationFrame(() => {
            this.focusLastInput();
        });
    };

    protected focusLastInput() {
        const namedElements = this.getNamedElements();

        if (namedElements.length) {
            namedElements[namedElements.length - 1].focus();
        }
    }

    protected renderDeleteButton(key: string): SlottedTemplateResult {
        const deleteOneGroup = () => {
            this.#setKeyedItems(this.#syncFromDOM().filter((entry) => entry.key !== key));
            this.dispatchChangeEvent();
        };

        return html`<button class="pf-c-button pf-m-control" type="button" @click=${deleteOneGroup}>
            <i class="fas fa-minus" aria-hidden="true"></i>
        </button>`;
    }

    render() {
        return html` <div class="pf-l-stack">
            ${repeat(
                this.#items,
                (item: Keyed<T>) => item.key,
                (item: Keyed<T>, idx) =>
                    html` <div class="ak-input-group" @change=${() => this.changeListener()}>
                        ${this.row(item.item, idx)}${this.renderDeleteButton(item.key)}
                    </div>`,
            )}
            <button class="pf-c-button pf-m-link" type="button" @click=${this.addNewGroup}>
                <span class="pf-c-button__icon pf-m-start">
                    <i class="fas fa-plus" aria-hidden="true"></i
                ></span>
                ${msg("Add entry")}
            </button>
        </div>`;
    }
}

export function akArrayInput<T>(properties: IArrayInput<T>) {
    return html`<ak-array-input ${spread(properties as unknown as Spread)}></ak-array-input>`;
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-array-input": ArrayInput<unknown>;
    }
}

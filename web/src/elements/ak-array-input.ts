import { AKControlElement } from "#elements/ControlElement";
import { SlottedTemplateResult, type Spread } from "#elements/types";
import { randomId } from "#elements/utils/randomId";

import { spread } from "@open-wc/lit-helpers";

import { msg } from "@lit/localize";
import { css, html, nothing } from "lit";
import { customElement, property, queryAll } from "lit/decorators.js";
import { repeat } from "lit/directives/repeat.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";

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

    // This magic creates a semi-reliable key on which Lit's `repeat` directive can control its
    // interaction. Without it, we get undefined behavior in the re-rendering of the array.
    @property({ type: Array, attribute: false })
    public set items(nextItems: T[]) {
        const previousItems = new Map(
            (this.#items ?? []).map((key, item) => [JSON.stringify(item), key]),
        );

        const resolvedItems = nextItems.map((item) => ({
            item,
            key: previousItems.get(JSON.stringify(item))?.key ?? randomId(),
        }));

        this.#items = resolvedItems;
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
        return Array.from(this.inputGroups ?? []).map(
            (group) => group.querySelector<HTMLInputElement & AKControlElement<T>>("[name]")!,
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

    protected changeListener = () => {
        this.items = this.itemsFromDOM();
        this.dispatchChangeEvent();
    };

    protected addNewGroup = () => {
        this.items = [...this.itemsFromDOM(), this.newItem()];
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

    protected renderDeleteButton(idx: number): SlottedTemplateResult {
        const deleteOneGroup = () => {
            this.items = [...this.items.slice(0, idx), ...this.items.slice(idx + 1)];
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
                        ${this.row(item.item, idx)}${this.renderDeleteButton(idx)}
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

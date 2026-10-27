import PFCheck from "@patternfly/patternfly/components/Check/check.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";

import Styles from "#elements/ak-checkbox-group/ak-checkbox-group.css";
import { FormAssociatedElement } from "#elements/forms/form-associated-element";
import { SlottedTemplateResult } from "#elements/types";

import { msg } from "@lit/localize";
import { html, PropertyValues, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { map } from "lit/directives/map.js";

export type CheckboxItem<T extends string = string> = { name: T; label: string | TemplateResult };

export type CheckboxPair<T extends string = string> = [name: T, label: string | TemplateResult];

export type CheckboxItemInit<T extends string = string> = CheckboxItem<T> | CheckboxPair<T>;

function* generateCheckboxKeyValuePairs(items: Iterable<CheckboxItemInit>): Iterable<CheckboxPair> {
    for (const item of items) {
        yield Array.isArray(item) ? item : [item.name, item.label];
    }
}

/**
 * Two selections are the same when they hold the same names. Hosts often compute `value` anew on
 * every render.
 */
function selectionChanged(nextValue: string[] | undefined, previousValue: string[] | undefined) {
    const next = new Set(nextValue ?? []);
    const previous = new Set(previousValue ?? []);

    return next.size !== previous.size || [...next].some((name) => !previous.has(name));
}

/**
 * CheckboxGroup renders a collection of checkboxes in a linear list. Multiple
 * checkboxes may be picked.
 *
 * `value` is the selection provided by the host. Assigning different names replaces the
 * selection. Re-assigning the same names keeps the user's choices. A form reset restores `value`.
 *
 * @class CheckboxGroup
 * @element ak-checkbox-group
 *
 * @attr {options} - An array of either `[string, string | TemplateResult]` or
 *     `{ name: string, label: string | TemplateResult }`. The first value or
 *     `name` field must be a valid HTML identifier compatible with the HTML
 *     `name` attribute.
 *
 * @attr {value} - An array of `name` values corresponding to the options that
 *     are selected when the element is rendered.
 *
 * @attr {name} - The name of this element as it will appear in any <form>
 *     transaction
 *
 * @attr {required} - If true and no values are chosen, the form reports a
 *     missing value.
 *
 * @event {input} - Fired when the component's value has changed. Current value
 *     as an array of `name` will be in the `Event.detail` field.
 *
 * @event {change} - Fired when the component's value has changed. Current value
 *     as an array of `name` will be in the `Event.detail` field.
 *
 * @csspart checkbox - The div containing the checkbox item and the label
 * @csspart label - the label
 * @csspart input - the input item
 * @csspart checkbox-group - the wrapper div with flexbox control
 *
 * ## Bigger hit area
 *
 * Providing properly formatted names for selections allows the element to
 * associate the label with the event, so the entire horizontal area from
 * checkbox to end-of-label will be the hit area.
 *
 * ## Form value
 *
 * Inside a <form>, the selection is submitted as one `name=value` entry per
 * chosen option, like `<select multiple>`.
 */
@customElement("ak-checkbox-group")
export class CheckboxGroup extends FormAssociatedElement<FormData | null, string[]> {
    static styles = [PFForm, PFCheck, Styles];

    @property({ type: Array })
    public options: CheckboxItemInit[] = [];

    @property({ type: Array, hasChanged: selectionChanged })
    public value: string[] = [];

    @state()
    protected values: string[] = [];

    //#region Lifecycle

    protected override willUpdate(changedProperties: PropertyValues<this>): void {
        super.willUpdate(changedProperties);

        if (changedProperties.has("value")) {
            this.values = [...(this.value ?? [])];
        }
    }

    protected override updated(changedProperties: PropertyValues<this>): void {
        super.updated(changedProperties);

        this.#syncValidity();
    }

    public formResetCallback(): void {
        this.values = [...(this.value ?? [])];
    }

    public formStateRestoreCallback(state: FormData | string | null): void {
        if (!(state instanceof FormData) || !this.name) return;

        this.values = state.getAll(this.name).filter((entry) => typeof entry === "string");
    }

    //#endregion

    //#region Value

    public toJSON(): string[] {
        return [...this.values];
    }

    #syncValidity(): void {
        let formData: FormData | null = null;

        if (this.name) {
            formData = new FormData();

            for (const name of this.values) {
                formData.append(this.name, name);
            }
        }

        this.internals.setFormValue(formData);

        if (this.required && !this.values.length) {
            this.internals.setValidity(
                { valueMissing: true },
                msg("A selection is required"),
                this.renderRoot.querySelector<HTMLInputElement>('input[type="checkbox"]') ??
                    undefined,
            );

            return;
        }

        this.internals.setValidity({});
    }

    //#endregion

    //#region Event Listeners

    #checkboxChanged = (event: Event): void => {
        event.stopPropagation();

        const checkboxes =
            this.renderRoot.querySelectorAll<HTMLInputElement>('input[type="checkbox"]');

        this.values = Array.from(checkboxes)
            .filter((checkbox) => checkbox.checked)
            .map((checkbox) => checkbox.name);

        for (const type of ["change", "input"]) {
            this.dispatchEvent(
                new CustomEvent(type, { bubbles: true, composed: true, detail: this.values }),
            );
        }
    };

    #stopInput = (event: Event): void => {
        event.stopPropagation();
    };

    //#endregion

    //#region Rendering

    protected renderCheckbox = ([name, label]: CheckboxPair): SlottedTemplateResult => {
        return html`<label part="label" for="ak-check-${name}" class="pf-c-check">
            <input
                part="input"
                @change=${this.#checkboxChanged}
                @input=${this.#stopInput}
                name=${name}
                class="pf-c-check__input"
                type="checkbox"
                .checked=${this.values.includes(name)}
                id="ak-check-${name}"
            />
            <div class="pf-c-check__label">${label}</div>
        </label>`;
    };

    protected override render(): SlottedTemplateResult {
        return html`<div part="checkbox-group" class="pf-c-form__group-control pf-m-stack">
            ${map(generateCheckboxKeyValuePairs(this.options), this.renderCheckbox)}
        </div>`;
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-checkbox-group": CheckboxGroup;
    }
}

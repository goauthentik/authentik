import { FormAssociatedElement } from "#elements/forms/form-associated-element";
import Styles from "#elements/forms/Radio.css";
import { SlottedTemplateResult } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";
import { isInteractiveElement } from "#elements/utils/interactivity";

import { IDGenerator } from "@goauthentik/core/id";

import { Jsonifiable } from "type-fest";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, PropertyValues } from "lit";
import { ref } from "lit-html/directives/ref.js";
import { repeat } from "lit-html/directives/repeat.js";
import { customElement, property } from "lit/decorators.js";

import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";

export interface RadioOption<T extends Jsonifiable | undefined> {
    label: string;
    description?: SlottedTemplateResult;
    className?: string;
    default?: boolean;
    value: T;
    disabled?: boolean;
}

export interface RadioChangeEventDetail<T> {
    value: T;
}

@customElement("ak-radio")
export class Radio<T extends Jsonifiable = never> extends FormAssociatedElement<string, T | null> {
    public static styles: CSSResult[] = [
        // ---
        PFRadio,
        PFForm,
        Styles,
    ];

    /**
     * Options to display in the radio group.
     *
     * Can be either an array of RadioOption<T> or a function returning such an array.
     */
    @property({ attribute: false })
    public options!: RadioOption<T>[] | (() => RadioOption<T>[]);

    #value: T | null = null;

    @property()
    public set value(nextValue: T) {
        if (nextValue === null) {
            return;
        }

        this.#value = nextValue;

        this.#syncValidity();
    }

    /**
     * The stringified value of the currently selected radio option.
     */
    public get value(): string {
        if (this.#value === null) {
            return "";
        }

        return typeof this.#value === "string" ? this.#value : JSON.stringify(this.#value);
    }

    #syncValidity() {
        this.internals.setFormValue(this.value);

        let message: string | undefined;
        const flags: ValidityStateFlags = {};

        if (this.required && !this.#value) {
            message = msg("This field is required.");
            flags.valueMissing = true;
        }

        this.internals.setValidity(flags, message, this.anchorRef.value);
    }

    /**
     * The raw value of the currently selected radio option.
     *
     * This is the value that will be submitted with the form when serialized.
     */
    public toJSON(): T | null {
        return this.#value;
    }

    #fieldID: string = this.name || IDGenerator.randomID();

    /**
     * Read the options, whether they're provided as a static array or a lazy function.
     */
    protected readOptions(): RadioOption<T>[] {
        return typeof this.options === "function" ? this.options() : this.options;
    }

    public override connectedCallback(): void {
        super.connectedCallback();

        if (this.getAttribute("tabindex") === null) {
            this.setAttribute("tabindex", "0");
        }

        this.role ||= "group";
    }

    // Set the value if it's not set already. Property changes inside the `willUpdate()` method do
    // not trigger an element update.
    public override willUpdate(changedProperties: PropertyValues<this>): void {
        super.willUpdate(changedProperties);

        if (!this.value) {
            const defaultOption = this.readOptions().find((opt) => opt.default);

            if (defaultOption) {
                this.value = defaultOption.value;
            }
        }
    }

    public override firstUpdated(changedProperties: PropertyValues<this>): void {
        super.firstUpdated(changedProperties);
        this.#syncValidity();
    }

    // When a user clicks on `type="radio"`, *two* events happen in rapid succession: the original
    // radio loses its setting, and the selected radio gains its setting. We want radio buttons to
    // present a unified event interface, so we prevent the event from triggering if the value is
    // already set.
    protected buildChangeListener(option: RadioOption<T>): (event: Event) => void {
        return (event: Event) => {
            // This is a controlled input. Stop the native event from escaping or affecting the
            // value. We'll do that ourselves.
            event.preventDefault();
            event.stopPropagation();

            if (option.disabled) {
                return;
            }

            this.value = option.value;

            this.dispatchEvent(
                new CustomEvent<RadioChangeEventDetail<T>>("change", {
                    detail: { value: option.value },
                    bubbles: true,
                    composed: true,
                }),
            );

            this.dispatchEvent(
                new CustomEvent<RadioChangeEventDetail<T>>("input", {
                    detail: { value: option.value },
                    bubbles: true,
                    composed: true,
                }),
            );
        };
    }

    protected renderRadio = (option: RadioOption<T>, index: number): SlottedTemplateResult => {
        const id = `${this.#fieldID}-${index}`;

        const changeListener = this.buildChangeListener(option);

        const clickListener = (event: Event) => {
            if (event.target instanceof HTMLInputElement && event.target.type === "radio") {
                return;
            }

            if (isInteractiveElement(event.target)) {
                return;
            }

            return changeListener(event);
        };

        const checked = option.value === this.#value;

        return html`<label
            class="pf-c-radio ${option.disabled ? "pf-m-disabled" : ""}"
            @click=${clickListener}
            part="option ${checked ? "checked" : ""} ${option.disabled ? "disabled" : ""}"
            for=${id}
            ><div class="pf-c-radio__label ${option.className ?? ""}" part="label">
                ${option.label}
            </div>
            <input
                ${index === 0 ? ref(this.anchorRef) : nothing}
                class="pf-c-radio__input"
                type="radio"
                name=${ifPresent(this.name)}
                aria-label=${option.label}
                id=${id}
                .checked=${checked}
                .disabled=${!!option.disabled}
                ?required=${this.required}
                @change=${changeListener}
                part="input"
            />

            ${option.description
                ? html`<span class="pf-c-radio__description" part="description"
                      >${option.description}</span
                  >`
                : null}
        </label>`;
    };

    protected override render(): SlottedTemplateResult {
        const options = this.readOptions();

        return html`<div
            class="pf-c-form__group-control pf-m-stack"
            ${ref(this.anchorRef)}
            part="control"
        >
            <slot></slot>
            ${repeat(options, (option) => option, this.renderRadio)}
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-radio": Radio<never>;
    }
}

export default Radio;
